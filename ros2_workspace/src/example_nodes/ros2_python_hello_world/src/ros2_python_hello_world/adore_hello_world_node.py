# ********************************************************************************
# Copyright (c) 2025 Contributors to the Eclipse Foundation
#
# See the NOTICE file(s) distributed with this work for additional
# information regarding copyright ownership.
#
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# https://www.eclipse.org/legal/epl-2.0
#
# SPDX-License-Identifier: EPL-2.0
# ********************************************************************************

import rclpy
from rclpy.node import Node

from adore_ros2_msgs.msg import Point2d

class AdoreHelloNode(Node):
    def __init__(self):
        super().__init__('adore_hello_world_node')

        self.topic_name = 'point2d_topic'
        
        if HAS_ADORE_MSGS:
            self.publisher_ = self.create_publisher(Point2d, self.topic_name, 10)
            self.subscription = self.create_subscription(Point2d, self.topic_name, self.listener_callback, 10)
        else:
            self.publisher_ = self.create_publisher(Point, self.topic_name, 10)
            self.subscription = self.create_subscription(Point, self.topic_name, self.listener_callback, 10)

        self.timer = self.create_timer(1.0, self.timer_callback)

    def timer_callback(self):
        if HAS_ADORE_MSGS:
            msg = Point2d()
            self.get_logger().info('Published empty Point2d')
        else:
            msg = Point()
            self.get_logger().info('Published empty Point')
        self.publisher_.publish(msg)

    def listener_callback(self, msg):
        if HAS_ADORE_MSGS:
            self.get_logger().info(f'Received Point2d: x={msg.x}, y={msg.y}')
        else:
            self.get_logger().info(f'Received Point: x={msg.x}, y={msg.y}')

def main(args=None):
    rclpy.init(args=args)
    node = AdoreHelloNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
