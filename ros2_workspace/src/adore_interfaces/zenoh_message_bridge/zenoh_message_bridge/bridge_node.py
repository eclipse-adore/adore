# ********************************************************************************
# Copyright (c) 2026 Contributors to the Eclipse Foundation
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

import os
import queue
import yaml
import zenoh
import rclpy
from rclpy.node import Node
from rclpy.executors import MultiThreadedExecutor
from .utils import load_msg_type, msg_to_bytes, bytes_to_msg

class ROS2ZenohBridge(Node):
    def __init__(self):
        super().__init__('zenoh_bridge_node')
        self.declare_parameter('config_path', '')
        self.declare_parameter('zenoh_router', 'tcp/localhost:7447')

        config_path = self.get_parameter('config_path').get_parameter_value().string_value
        if not config_path or not os.path.exists(config_path):
            self.get_logger().error(f"Config file not found: {config_path}")
            return

        try:
            with open(config_path, 'r') as f:
                self.config = yaml.safe_load(f)
        except Exception as e:
            self.get_logger().error(f"Failed to parse config with yq: {e}")
            return

        self.zenoh_session = None
        self.zenoh_subs = []
        self.zenoh_pubs = {}
        self.ros_subs = []
        self.ros_pubs = {}
        self._z2r_queue = queue.Queue()

        self._setup_zenoh()
        self._setup_ros2_to_zenoh()
        self._setup_zenoh_to_ros2()
        self.create_timer(0.01, self._drain_z2r_queue)
        
    def _setup_zenoh(self):
        endpoint = self.get_parameter('zenoh_router').get_parameter_value().string_value
        z_config = zenoh.Config()
        z_config.insert_json5('connect/endpoints', f'["{endpoint}"]')
        self.zenoh_session = zenoh.open(z_config)
        self.get_logger().info(f'Connected to Zenoh: {endpoint}')

    def _setup_ros2_to_zenoh(self):
        for mapping in self.config.get('ros2_to_zenoh', []):
            ros_topic = mapping['ros_topic']
            zenoh_key = mapping['zenoh_key']
            msg_type = load_msg_type(mapping.get('msg_type', 'std_msgs/msg/String'))
            pub = self.zenoh_session.declare_publisher(zenoh_key)
            self.zenoh_pubs[ros_topic] = pub
            cb = lambda msg, p=pub, k=zenoh_key: (p.put(msg_to_bytes(msg)), self.get_logger().debug(f'R2Z: {k}'))
            self.ros_subs.append(self.create_subscription(msg_type, ros_topic, cb, 10))

    def _setup_zenoh_to_ros2(self):
        for mapping in self.config.get('zenoh_to_ros2', []):
            z_key = mapping['zenoh_key']
            ros_topic = mapping['ros_topic']
            m_type = load_msg_type(mapping.get('msg_type', 'std_msgs/msg/String'))
            pub = self.create_publisher(m_type, ros_topic, 10)
            self.ros_pubs[z_key] = pub
            def z_cb(sample, p=pub, mt=m_type, t=ros_topic):
                try:
                    self._z2r_queue.put((p, bytes_to_msg(sample.payload.to_bytes(), mt)))
                except Exception as e:
                    self.get_logger().error(f'Deser failed on {t}: {e}')
            self.zenoh_subs.append(self.zenoh_session.declare_subscriber(z_key, z_cb))

    def _drain_z2r_queue(self):
        while not self._z2r_queue.empty():
            pub, msg = self._z2r_queue.get_nowait()
            pub.publish(msg)

    def shutdown(self):
        for s in self.zenoh_subs: s.undeclare()
        if self.zenoh_session: self.zenoh_session.close()

def main(args=None):
    rclpy.init(args=args)
    node = ROS2ZenohBridge()
    executor = MultiThreadedExecutor()
    executor.add_node(node)
    try:
        executor.spin()
    except KeyboardInterrupt:
        pass
    finally:
        node.shutdown()
        node.destroy_node()
        rclpy.shutdown()
