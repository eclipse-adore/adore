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

import os
import pytest
import launch
import launch_testing
import launch_testing.actions
import launch.launch_description_sources
import rclpy
from rclpy.node import Node
import unittest
import time

from adore_ros2_msgs.msg import *


@pytest.mark.launch_test
def generate_test_description():
    launch_file = os.path.join(
        os.path.dirname(__file__),
        '..', 'adore_simulation_scenarios', 'simulation_test.launch.py'
    )

    return (
        launch.LaunchDescription([
            launch.actions.IncludeLaunchDescription(
                launch.launch_description_sources.PythonLaunchDescriptionSource(
                    launch_file)
            ),
            launch_testing.actions.ReadyToTest()
        ]),
        {}
    )


class TopicSubscriptionTest(unittest.TestCase):
    topic_map = {
        '/ego_vehicle/vehicle_state_dynamic': VehicleStateDynamic,
        '/ego_vehicle/trajectory_decision': Trajectory,
        '/ego_vehicle/next_vehicle_command': VehicleCommand,
    }

    @classmethod
    def setUpClass(cls):
        rclpy.init()
        cls.node = rclpy.create_node('test_topic_subscriber')
        cls.received_msgs = {topic: [] for topic in cls.topic_map}
        cls.subscriptions = []

        for topic, msg_type in cls.topic_map.items():
            sub = cls.node.create_subscription(
                msg_type,
                topic,
                lambda msg, t=topic: cls.received_msgs[t].append(msg),
                10
            )
            cls.subscriptions.append(sub)

    @classmethod
    def tearDownClass(cls):
        for sub in cls.subscriptions:
            cls.node.destroy_subscription(sub)
        cls.node.destroy_node()
        rclpy.shutdown()


# Dynamically generate one test per topic
def _make_test(topic):
    def test(self):
        timeout = 10.0
        start_time = time.time()
        while time.time() - start_time < timeout:
            rclpy.spin_once(self.node, timeout_sec=0.1)
            if self.received_msgs[topic]:
                break
        self.assertTrue(
            self.received_msgs[topic],
            f"No messages received on topic: {topic}"
        )
    return test


for topic in TopicSubscriptionTest.topic_map:
    test_method = _make_test(topic)
    test_name = f'test_topic_{topic.strip("/").replace("/", "_")}'
    setattr(TopicSubscriptionTest, test_name, test_method)
