import os
import signal
import threading
import time
import yaml
import numpy as np
import cv2
import rclpy
from rclpy.node import Node
from rclpy.executors import MultiThreadedExecutor
from sensor_msgs.msg import Image, CompressedImage
from ament_index_python.packages import get_package_share_directory


_ENCODING_CONVERSIONS = {
    'rgb8':  cv2.COLOR_RGB2BGR,
    'mono8': None,
    'bgr8':  None,
}

_FREQ_WINDOW    = 30
_HEADER_PADDING = 10
_HEADER_LINE_H  = 22
_HEADER_SCALE   = 0.50


def _to_bgr(frame: np.ndarray, encoding: str) -> np.ndarray:
    conversion = _ENCODING_CONVERSIONS.get(encoding)
    if conversion is not None:
        return cv2.cvtColor(frame, conversion)
    return frame


def _raw_msg_to_frame(msg: Image) -> tuple[np.ndarray, str]:
    channels = 1 if msg.encoding == 'mono8' else 3
    frame = np.frombuffer(msg.data, dtype=np.uint8).reshape((msg.height, msg.width, channels))
    return _to_bgr(frame, msg.encoding), msg.encoding


def _compressed_msg_to_frame(msg: CompressedImage) -> tuple[np.ndarray, str]:
    buf = np.frombuffer(msg.data, dtype=np.uint8)
    frame = cv2.imdecode(buf, cv2.IMREAD_COLOR)
    if frame is None:
        raise ValueError(f'cv2.imdecode failed for format: {msg.format}')
    return frame, msg.format


def _draw_label(img: np.ndarray, text: str, pos: tuple, scale: float = 0.55) -> None:
    cv2.putText(img, text, pos, cv2.FONT_HERSHEY_SIMPLEX, scale, (0, 0, 0),   3, cv2.LINE_AA)
    cv2.putText(img, text, pos, cv2.FONT_HERSHEY_SIMPLEX, scale, (255, 255, 255), 1, cv2.LINE_AA)


def _draw_header_overlay(display: np.ndarray, header, encoding: str, shape: tuple) -> None:
    stamp     = header.stamp
    stamp_sec = stamp.sec + stamp.nanosec * 1e-9
    lines = [
        f'frame_id : {header.frame_id if header.frame_id else "(empty)"}',
        f'stamp    : {stamp.sec}.{stamp.nanosec:09d}  ({stamp_sec:.6f} s)',
        f'encoding : {encoding}',
        f'size     : {shape[1]} x {shape[0]}',
    ]

    panel_w = 380
    panel_h = _HEADER_PADDING * 2 + len(lines) * _HEADER_LINE_H
    x0 = display.shape[1] - panel_w - _HEADER_PADDING
    y0 = _HEADER_PADDING

    overlay = display.copy()
    cv2.rectangle(overlay, (x0, y0), (x0 + panel_w, y0 + panel_h), (30, 30, 30), -1)
    cv2.addWeighted(overlay, 0.6, display, 0.4, 0, display)

    cv2.rectangle(display, (x0, y0), (x0 + panel_w, y0 + panel_h), (180, 180, 180), 1)

    for i, line in enumerate(lines):
        ty = y0 + _HEADER_PADDING + (i + 1) * _HEADER_LINE_H - 4
        cv2.putText(display, line, (x0 + 8, ty),
                    cv2.FONT_HERSHEY_SIMPLEX, _HEADER_SCALE, (200, 200, 200), 1, cv2.LINE_AA)


class ViewerNode(Node):
    def __init__(self):
        super().__init__('viewer_node')
        self._shutdown       = threading.Event()
        self._display_thread = None

        self.declare_parameter('config_path', '')

        config_path = self.get_parameter('config_path').get_parameter_value().string_value
        if not config_path:
            config_path = os.path.join(
                get_package_share_directory('ros_image_streamer'),
                'config', 'viewer_config.yaml'
            )

        if not os.path.exists(config_path):
            self.get_logger().error(f'Config not found: {config_path}')
            self._shutdown.set()
            raise RuntimeError(f'Config not found: {config_path}')

        with open(config_path, 'r') as f:
            cfg = yaml.safe_load(f)

        self._topic       = cfg.get('topic',       '/camera/image_raw')
        self._window_name = cfg.get('window_name', 'ROS Image Viewer')
        self._queue_depth = int(cfg.get('queue_depth', 10))
        self._compressed  = bool(cfg.get('compressed', False))

        self._latest_frame    = None
        self._latest_header   = None
        self._latest_encoding = ''
        self._frame_lock      = threading.Lock()
        self._show_header     = False

        self._msg_times: list[float] = []
        self._freq_lock  = threading.Lock()
        self._last_msg_t: float | None = None

        if self._compressed:
            self._sub = self.create_subscription(
                CompressedImage,
                self._topic,
                self._compressed_image_callback,
                self._queue_depth,
            )
        else:
            self._sub = self.create_subscription(
                Image,
                self._topic,
                self._raw_image_callback,
                self._queue_depth,
            )

        self._display_thread = threading.Thread(target=self._display_loop, daemon=True)
        self._display_thread.start()
        mode = 'compressed' if self._compressed else 'raw'
        self.get_logger().info(f'Viewing topic: {self._topic} ({mode})')

    def _handle_frame(self, header, frame: np.ndarray, encoding: str) -> None:
        now = time.monotonic()
        with self._frame_lock:
            self._latest_frame    = frame
            self._latest_header   = header
            self._latest_encoding = encoding
        with self._freq_lock:
            self._last_msg_t = now
            self._msg_times.append(now)
            if len(self._msg_times) > _FREQ_WINDOW:
                self._msg_times.pop(0)

    def _raw_image_callback(self, msg: Image) -> None:
        try:
            frame, encoding = _raw_msg_to_frame(msg)
        except Exception as e:
            self.get_logger().error(f'Failed to decode frame: {e}')
            return
        self._handle_frame(msg.header, frame, encoding)

    def _compressed_image_callback(self, msg: CompressedImage) -> None:
        try:
            frame, encoding = _compressed_msg_to_frame(msg)
        except Exception as e:
            self.get_logger().error(f'Failed to decode compressed frame: {e}')
            return
        self._handle_frame(msg.header, frame, encoding)

    def _get_stats(self) -> tuple[bool, float]:
        with self._freq_lock:
            if self._last_msg_t is None:
                return False, 0.0
            stale = (time.monotonic() - self._last_msg_t) > 2.0
            if stale:
                return False, 0.0
            if len(self._msg_times) < 2:
                return True, 0.0
            span = self._msg_times[-1] - self._msg_times[0]
            hz = (len(self._msg_times) - 1) / span if span > 0 else 0.0
            return True, hz

    def _display_loop(self):
        cv2.namedWindow(self._window_name, cv2.WINDOW_NORMAL)
        while not self._shutdown.is_set():
            with self._frame_lock:
                frame    = self._latest_frame
                header   = self._latest_header
                encoding = self._latest_encoding

            if frame is not None:
                display = frame.copy()
                active, hz = self._get_stats()

                if self._show_header and header is not None:
                    _draw_header_overlay(display, header, encoding, frame.shape)

                status_color = (0, 220, 0) if active else (0, 0, 220)
                cv2.circle(display, (14, 14), 7, (0, 0, 0), -1)
                cv2.circle(display, (14, 14), 6, status_color, -1)

                _draw_label(display, self._topic, (28, 20))

                freq_text = f'{hz:.1f} Hz' if active and hz > 0 else ('active' if active else 'no signal')
                _draw_label(display, freq_text, (28, 40))

                cv2.imshow(self._window_name, display)
            else:
                blank = np.zeros((240, 480, 3), dtype=np.uint8)
                active, _ = self._get_stats()
                status_color = (0, 220, 0) if active else (0, 0, 220)
                cv2.circle(blank, (14, 14), 7, (0, 0, 0), -1)
                cv2.circle(blank, (14, 14), 6, status_color, -1)
                _draw_label(blank, self._topic, (28, 20))
                _draw_label(blank, 'waiting...', (28, 40))
                cv2.imshow(self._window_name, blank)

            key = cv2.waitKey(1) & 0xFF
            if key == ord('q') or key == 27:
                self.get_logger().info('Viewer closed by user')
                self._shutdown.set()
                break
            elif key == ord('h'):
                self._show_header = not self._show_header

        cv2.destroyAllWindows()

    def shutdown(self):
        self._shutdown.set()
        if self._display_thread is not None and self._display_thread.is_alive():
            self._display_thread.join(timeout=2.0)
        cv2.destroyAllWindows()

    def is_shutdown(self) -> bool:
        return self._shutdown.is_set()


def main(args=None):
    rclpy.init(args=args)
    try:
        node = ViewerNode()
    except RuntimeError:
        rclpy.shutdown()
        return

    executor = MultiThreadedExecutor()
    executor.add_node(node)

    shutdown_event = threading.Event()

    def _signal_handler(sig, frame):
        shutdown_event.set()
        node.shutdown()

    signal.signal(signal.SIGINT,  _signal_handler)
    signal.signal(signal.SIGTERM, _signal_handler)

    try:
        while not shutdown_event.is_set() and not node.is_shutdown():
            executor.spin_once(timeout_sec=0.1)
    finally:
        node.shutdown()
        executor.shutdown()
        node.destroy_node()
        rclpy.shutdown()
