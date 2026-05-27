import signal
import threading
import numpy as np
import cv2
import rclpy
from rclpy.node import Node
from rclpy.executors import MultiThreadedExecutor
from sensor_msgs.msg import Image


_ENCODING_CONVERSIONS = {
    'rgb8':  cv2.COLOR_RGB2BGR,
    'mono8': None,
    'bgr8':  None,
}


def _to_bgr(frame: np.ndarray, encoding: str) -> np.ndarray:
    conversion = _ENCODING_CONVERSIONS.get(encoding)
    if conversion is not None:
        return cv2.cvtColor(frame, conversion)
    return frame


def _msg_to_frame(msg: Image) -> np.ndarray:
    channels = 1 if msg.encoding == 'mono8' else 3
    frame = np.frombuffer(msg.data, dtype=np.uint8).reshape((msg.height, msg.width, channels))
    return _to_bgr(frame, msg.encoding)


class ViewerNode(Node):
    def __init__(self):
        super().__init__('viewer_node')
        self.declare_parameter('topic',       '/camera/image_raw')
        self.declare_parameter('window_name', 'ROS Image Viewer')
        self.declare_parameter('queue_depth', 10)

        self._topic       = self.get_parameter('topic').get_parameter_value().string_value
        self._window_name = self.get_parameter('window_name').get_parameter_value().string_value
        self._queue_depth = self.get_parameter('queue_depth').get_parameter_value().integer_value

        self._latest_frame = None
        self._frame_lock   = threading.Lock()
        self._shutdown     = threading.Event()

        self._sub = self.create_subscription(
            Image,
            self._topic,
            self._image_callback,
            self._queue_depth,
        )

        self._display_thread = threading.Thread(target=self._display_loop, daemon=True)
        self._display_thread.start()
        self.get_logger().info(f'Viewing topic: {self._topic}')

    def _image_callback(self, msg: Image):
        try:
            frame = _msg_to_frame(msg)
        except Exception as e:
            self.get_logger().error(f'Failed to decode frame: {e}')
            return

        with self._frame_lock:
            self._latest_frame = frame

    def _display_loop(self):
        cv2.namedWindow(self._window_name, cv2.WINDOW_NORMAL)
        while not self._shutdown.is_set():
            with self._frame_lock:
                frame = self._latest_frame

            if frame is not None:
                display = frame.copy()
                cv2.putText(
                    display, self._topic,
                    (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0),   3, cv2.LINE_AA
                )
                cv2.putText(
                    display, self._topic,
                    (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1, cv2.LINE_AA
                )
                cv2.imshow(self._window_name, display)

            key = cv2.waitKey(1) & 0xFF
            if key == ord('q') or key == 27:
                self.get_logger().info('Viewer closed by user')
                self._shutdown.set()
                break

        cv2.destroyAllWindows()

    def shutdown(self):
        self._shutdown.set()
        if self._display_thread.is_alive():
            self._display_thread.join(timeout=2.0)
        cv2.destroyAllWindows()

    def is_shutdown(self) -> bool:
        return self._shutdown.is_set()


def main(args=None):
    rclpy.init(args=args)
    node = ViewerNode()
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
