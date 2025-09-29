"""A minimal ROS 2 Python node that logs "Hello, world" and a random NumPy array on a timer."""
import rclpy
from rclpy.node import Node
import numpy as np

class HelloWorldNode(Node):
    def __init__(self):
        super().__init__('hello_world')
        self.get_logger().info('HelloWorldNode with NumPy started')
        self._count = 0
        self._timer = self.create_timer(1.0, self.timer_callback)
    
    def timer_callback(self):
        self._count += 1
        random_array = np.random.rand(3)
        self.get_logger().info(f'Hello, world! count: {self._count}, random: {random_array}')

def main(args=None):
    rclpy.init(args=args)
    node = HelloWorldNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info('KeyboardInterrupt, shutting down')
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
