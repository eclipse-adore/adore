import pytest
import rclpy
import time
from rclpy.node import Node
from rclpy.qos import QoSProfile, QoSReliabilityPolicy
import subprocess
import os

import importlib

from test_helpers import kill_process_and_children

class TopicMonitor(Node):
    """A node that dynamically discovers topics but only tests required ones."""

    def __init__(self, required_topics):
        super().__init__('topic_monitor')

        self.required_topics = required_topics
        self.received_messages = {topic_name: False for topic_name in required_topics}
        self.dynamic_subscriptions = {}
        self.qos = QoSProfile(depth=10, reliability=QoSReliabilityPolicy.BEST_EFFORT)

        # Start discovery loop
        self.timer = self.create_timer(1.0, self.update_subscriptions)

    def update_subscriptions(self):
        """Dynamically discover topics and subscribe only to required ones."""
        topics = self.get_topic_names_and_types()
        for topic_name, msg_types in topics:
            if topic_name in self.required_topics and msg_types and not self.dynamic_subscriptions.get(topic_name):
                msg_type = self.get_msg_type(msg_types[0])  # Use first available message type
                if msg_type:
                    self.received_messages[topic_name] = False
                    sub = self.create_subscription(
                        msg_type,
                        topic_name,
                        lambda msg, topic=topic_name: self._message_callback(topic),
                        self.qos
                    )
                    self.dynamic_subscriptions[topic_name] = sub
                    self.get_logger().info(f"Subscribed to required topic: {topic_name}")

    def _message_callback(self, topic):
        """Callback function to mark a required topic as active when a message is received."""
        self.received_messages[topic] = True

    def get_msg_type(self, type_name):
        """Dynamically import a ROS 2 message type from its string representation."""
        try:
            pkg,_, msg = type_name.split('/')
            module = importlib.import_module(f"{pkg}.msg")  # Import the message module
            return getattr(module, msg)  # Get the specific message type class
        except (ImportError, AttributeError, ValueError) as e:
            self.get_logger().warn(f"Failed to import message type '{type_name}': {e}")
            return None

def base_topic_test(required_topics, launch_file, timeout=10.0):
    """Decorator to create a base topic test class with required topics."""

    print("launch file: ", launch_file)
    # Start the launch file in a new process group (so we can cleanly kill it)
    process = subprocess.Popen(
        ["ros2", "launch", launch_file],
        preexec_fn=os.setsid  # Creates a new process group
    )

    # Start the topic monitor
    rclpy.init()
    topic_monitor = TopicMonitor(required_topics)
    start_time = time.time()

    while time.time() - start_time < timeout:
        rclpy.spin_once(topic_monitor, timeout_sec=0.1)
        if all(topic_monitor.received_messages.values()):
            break

    rclpy.shutdown()

    # Kill the entire launch process group
    kill_process_and_children(process.pid)

    # Check topics that are published
    for topic, received in topic_monitor.received_messages.items():
        assert received, f"❌ Topic {topic} was not received."

