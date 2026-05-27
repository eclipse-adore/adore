import os
import signal
import threading
import yaml
import cv2
import numpy as np
import rclpy
from rclpy.node import Node
from rclpy.executors import MultiThreadedExecutor
from sensor_msgs.msg import Image
from ament_index_python.packages import get_package_share_directory


_ENCODING_CHANNELS = {
    'bgr8':  3,
    'rgb8':  3,
    'mono8': 1,
}


def _open_device(cfg: dict) -> cv2.VideoCapture:
    cap = cv2.VideoCapture(cfg['path'], cv2.CAP_V4L2)
    fourcc = cfg.get('fourcc', 'MJPG')
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*fourcc))
    cap.set(cv2.CAP_PROP_FRAME_WIDTH,  cfg.get('width',  1280))
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, cfg.get('height', 720))
    cap.set(cv2.CAP_PROP_FPS,          cfg.get('fps',    30))
    return cap


def _open_ffmpeg(cfg: dict) -> cv2.VideoCapture:
    url = cfg['url']
    cap = cv2.VideoCapture(url, cv2.CAP_FFMPEG)
    for prop, value in cfg.get('options', {}).items():
        cap.set(getattr(cv2, prop, prop), value)
    return cap


class StreamingNode(Node):
    def __init__(self):
        super().__init__('streaming_node')
        self.declare_parameter('config_path', '')

        config_path = self.get_parameter('config_path').get_parameter_value().string_value
        if not config_path:
            config_path = os.path.join(
                get_package_share_directory('ros_image_streamer'),
                'config', 'streamer_config.yaml'
            )

        if not os.path.exists(config_path):
            self.get_logger().error(f'Config not found: {config_path}')
            return

        with open(config_path, 'r') as f:
            self._cfg = yaml.safe_load(f)

        self._encoding    = self._cfg.get('encoding', 'bgr8')
        self._topic       = self._cfg.get('publish_topic', '/camera/image_raw')
        self._queue_depth = int(self._cfg.get('queue_depth', 10))
        self._cap         = None
        self._shutdown    = threading.Event()

        self._pub = self.create_publisher(Image, self._topic, self._queue_depth)
        self._open_capture()

        self._capture_thread = threading.Thread(target=self._capture_loop, daemon=True)
        self._capture_thread.start()
        self.get_logger().info(f'Streaming on {self._topic} [{self._encoding}]')

    def _open_capture(self):
        source_type = self._cfg.get('source_type', 'device')
        if source_type == 'ffmpeg':
            self._cap = _open_ffmpeg(self._cfg.get('ffmpeg', {}))
            label = self._cfg.get('ffmpeg', {}).get('url', '')
        else:
            self._cap = _open_device(self._cfg.get('device', {'path': '/dev/video0'}))
            label = self._cfg.get('device', {}).get('path', '/dev/video0')

        if not self._cap.isOpened():
            self.get_logger().error(f'Failed to open source: {label}')
        else:
            self.get_logger().info(f'Opened source: {label}')

    def _frame_to_msg(self, frame: np.ndarray) -> Image:
        if self._encoding == 'rgb8':
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        elif self._encoding == 'mono8':
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        msg = Image()
        msg.header.stamp    = self.get_clock().now().to_msg()
        msg.header.frame_id = 'camera'
        msg.height          = frame.shape[0]
        msg.width           = frame.shape[1]
        msg.encoding        = self._encoding
        msg.is_bigendian    = False
        msg.step            = frame.shape[1] * _ENCODING_CHANNELS.get(self._encoding, 3)
        msg.data            = frame.tobytes()
        return msg

    def _capture_loop(self):
        while not self._shutdown.is_set():
            if self._cap is None or not self._cap.isOpened():
                self._shutdown.wait(1.0)
                continue

            ret, frame = self._cap.read()
            if not ret:
                self.get_logger().warn('Failed to read frame, retrying...')
                self._shutdown.wait(0.1)
                continue

            self._pub.publish(self._frame_to_msg(frame))

    def shutdown(self):
        self._shutdown.set()
        if self._capture_thread.is_alive():
            self._capture_thread.join(timeout=2.0)
        if self._cap is not None:
            self._cap.release()


def main(args=None):
    rclpy.init(args=args)
    node = StreamingNode()
    executor = MultiThreadedExecutor()
    executor.add_node(node)

    shutdown_event = threading.Event()

    def _signal_handler(sig, frame):
        shutdown_event.set()

    signal.signal(signal.SIGINT,  _signal_handler)
    signal.signal(signal.SIGTERM, _signal_handler)

    try:
        while not shutdown_event.is_set():
            executor.spin_once(timeout_sec=0.1)
    finally:
        node.shutdown()
        executor.shutdown()
        node.destroy_node()
        rclpy.shutdown()
