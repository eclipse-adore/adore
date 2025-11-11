# util/ros_message_importer.py
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

"""
ros_message_importer.py

Automatically detects and imports all available ROS 1 or ROS 2 message types
from installed packages and makes them accessible for dynamic usage.
"""

import sys
import importlib
import logging

# Configure basic logging for this utility
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')


class ROSMessageImporter:
    _msg_classes = {}
    _imported_flag = False

    @staticmethod
    def import_all_messages():
        if ROSMessageImporter._imported_flag:
            return

        try:
            import rclpy
            logging.info("Detected ROS 2")
            ROSMessageImporter._import_ros2_messages()
        except ImportError:
            try:
                import rospy  # noqa
                logging.info("Detected ROS 1")
                ROSMessageImporter._import_ros1_messages()
            except ImportError:
                logging.error(
                    "Neither ROS 1 nor ROS 2 is detected. Ensure ROS environment is sourced.")
                raise RuntimeError(
                    "Neither ROS 1 nor ROS 2 is detected. Ensure ROS environment is sourced.")

        ROSMessageImporter._imported_flag = True

    @staticmethod
    def _import_ros2_messages():
        import ament_index_python.packages

        all_packages = ament_index_python.packages.get_packages_with_prefixes().keys()
        # Look for packages ending in _msgs or just msgs (more robust)
        msg_packages = [
            pkg for pkg in all_packages if pkg.endswith(('_msgs', 'msgs'))]

        logging.info(
            f"Loading {len(msg_packages)} potential ROS 2 message packages...")

        total_loaded = 0
        for package in msg_packages:
            try:
                # ROS 2 message modules are typically in pkg_name.msg
                module = importlib.import_module(f"{package}.msg")
                package_count = 0

                for attr in dir(module):
                    if not attr.startswith('_'):
                        cls = getattr(module, attr)
                        # Check if it looks like a message class
                        if hasattr(cls, "__slots__") or hasattr(cls, "get_fields_and_field_types"):
                            # Store both the ROS 2 standard (pkg/msg/Type) and a shortened version (pkg/Type)
                            # for easier lookup compatibility.
                            key_full = f"{package}/msg/{attr}"
                            key_short = f"{package}/{attr}"
                            ROSMessageImporter._msg_classes[key_full] = cls
                            ROSMessageImporter._msg_classes[key_short] = cls
                            package_count += 1

                if package_count > 0:
                    logging.debug(
                        f"Loaded {package_count} messages from {package}")
                    total_loaded += package_count

            except ImportError:
                logging.debug(
                    f"Package {package} has no msg module, skipping.")
            except Exception as e:
                logging.warning(f"Error loading messages from {package}: {e}")

        logging.info(f"Total ROS 2 message types loaded: {total_loaded}")

    @staticmethod
    def _import_ros1_messages():
        import rosmsg
        import rospkg

        rospack = rospkg.RosPack()
        packages = rospack.list()

        all_messages = []
        for package in packages:
            try:
                # rosmsg.list_msgs returns fully qualified names (package/MsgType)
                msgs = rosmsg.list_msgs(package)
                all_messages.extend(msgs)
            except rospkg.common.ResourceNotFound:
                logging.debug(f"Package {package} not found, skipping.")

        if not all_messages:
            logging.warning("No ROS 1 messages found. Ensure ROS is sourced.")
            return

        logging.info(
            f"Attempting to load {len(all_messages)} ROS 1 message types...")

        total_loaded = 0
        for msg in all_messages:
            try:
                package, msg_type = msg.split("/")
                # ROS 1 message modules are typically in pkg_name.msg
                module = importlib.import_module(f"{package}.msg")
                cls = getattr(module, msg_type, None)
                if cls:
                    ROSMessageImporter._msg_classes[msg] = cls
                    total_loaded += 1
                else:
                    logging.debug(f"Failed to load class for {msg}")
            except (ModuleNotFoundError, AttributeError) as e:
                logging.debug(f"Error loading {msg}: {e}")

        logging.info(f"Total ROS 1 message types loaded: {total_loaded}")

    @staticmethod
    def get_class(datatype: str):
        """
        Retrieves the Python class for a given ROS message datatype string.
        Handles both ROS 1 (pkg/MsgType) and ROS 2 (pkg/msg/MsgType) formats.
        """
        if datatype in ROSMessageImporter._msg_classes:
            return ROSMessageImporter._msg_classes[datatype]

        # Try normalizing ROS 2 format "pkg/msg/MsgType" to "pkg/MsgType"
        normalized = datatype.replace("/msg/", "/")
        if normalized != datatype and normalized in ROSMessageImporter._msg_classes:
            return ROSMessageImporter._msg_classes[normalized]

        return None

    @staticmethod
    def list_all_loaded():
        """Display all loaded message types for debug purposes."""
        logging.info(
            f"\nAll loaded message types ({len(ROSMessageImporter._msg_classes)}):")
        for msg_type in sorted(ROSMessageImporter._msg_classes.keys()):
            print(f"  {msg_type}")


if __name__ == "__main__":
    ROSMessageImporter.import_all_messages()

    ROSMessageImporter.list_all_loaded()

    # Test common message types
    test_msgs = ["std_msgs/String", "geometry_msgs/Twist", "sensor_msgs/Image",
                 "sensor_msgs/msg/Imu", "std_msgs/msg/String"]

    print("\nTesting specific message types:")
    for msg in test_msgs:
        msg_class = ROSMessageImporter.get_class(msg)
        if msg_class:
            print(f"✅ Successfully loaded {msg}: {msg_class}")
        else:
            print(f"❌ Failed to load {msg}")
