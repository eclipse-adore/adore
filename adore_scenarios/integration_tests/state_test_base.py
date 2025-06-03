import pytest
import rclpy
import time
import os
import signal
import subprocess
import psutil
import math
from rclpy.node import Node
from rclpy.qos import QoSProfile, QoSReliabilityPolicy
from adore_ros2_msgs.msg import VehicleStateDynamic  # Replace with actual package if needed

from test_helpers import kill_process_and_children

class VehicleStateMonitor(Node):
    """A node that listens to VehicleStateDynamic and checks proximity to given points."""

    def __init__(self, target_points, distance_threshold):
        super().__init__('vehicle_state_monitor')

        self.target_points = target_points  # List of (x, y) positions
        self.distance_threshold = distance_threshold
        self.vehicle_reached_targets = {point: False for point in self.target_points}

        qos = QoSProfile(depth=10, reliability=QoSReliabilityPolicy.BEST_EFFORT)
        self.subscription = self.create_subscription(
            VehicleStateDynamic,
            "ego_vehicle/vehicle_state/dynamic", 
            self.vehicle_state_callback,
            qos
        )

    def vehicle_state_callback(self, msg):
        """Checks if the vehicle state is within range of any target points."""
        vehicle_x, vehicle_y = msg.x, msg.y

        for target in self.target_points:
            target_x, target_y = target
            distance = math.sqrt((vehicle_x - target_x) ** 2 + (vehicle_y - target_y) ** 2)
            
            if distance <= self.distance_threshold:
                self.vehicle_reached_targets[target] = True
                self.get_logger().info(f"✅ Vehicle reached target: {target} (Distance: {distance:.2f}m)")

    def wait_for_targets(self, timeout=10.0):
        """Waits for the vehicle to reach any of the target points within a timeout."""
        start_time = time.time()
        while time.time() - start_time < timeout:
            rclpy.spin_once(self, timeout_sec=0.1)
            if all(self.vehicle_reached_targets.values()):
                return True
        return False


def base_vehicle_state_test(launch_file, target_points, timeout, distance_threshold=2.0):
    """
    Runs a ROS 2 launch file, subscribes to /vehicle/state, and checks if the vehicle reaches given points.
    
    :param launch_file: Name of the ROS 2 launch file to run.
    :param target_points: List of (x, y) tuples representing target positions.
    :param distance_threshold: Maximum allowed distance from the target point to consider it reached.
    """
    # Start the ROS 2 launch file
    process = subprocess.Popen(
        ["ros2", "launch", launch_file],
        preexec_fn=os.setsid
    )

    # Initialize the ROS node
    rclpy.init()
    vehicle_monitor = VehicleStateMonitor(target_points, distance_threshold)
    reached = vehicle_monitor.wait_for_targets(timeout)

    rclpy.shutdown()
    kill_process_and_children(process.pid)

    # Check if all targets were reached
    assert reached, "❌ Vehicle did not reach all required target points within the time limit!"
