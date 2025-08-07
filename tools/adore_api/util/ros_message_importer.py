"""
ros_message_importer.py

Automatically detects and imports all available ROS 1 or ROS 2 message types
from installed packages and makes them accessible for dynamic usage.

This module provides a unified interface to:
- Detect whether the environment is ROS 1 or ROS 2.
- Load all message classes from available message packages.
- Retrieve message classes by name (e.g., "std_msgs/String", "sensor_msgs/msg/Imu").
- List all successfully loaded message types.

Usage:
    python ros_message_importer.py

    This will:
        - Attempt to detect and load messages from either ROS 1 or ROS 2.
        - Print a summary of loaded message types.
        - Test importing some common message types.

Class:
    ROSMessageImporter:
        Static class that manages the importing and retrieval of ROS message classes.

        Methods:
            - import_all_messages(): Detect and import all ROS 1/2 messages.
            - get_class(datatype): Return the class for a given message type string.
            - list_all_loaded(): Print all currently loaded message types.

Dependencies:
    - ROS 1: rospy, rosmsg, rospkg
    - ROS 2: rclpy, ament_index_python

Note:
    This script assumes the ROS environment is properly sourced. If neither ROS 1
    nor ROS 2 is detected, it will raise a RuntimeError.

"""


import sys
import importlib

class ROSMessageImporter:
    _msg_classes = {}

    @staticmethod
    def import_all_messages():
        try:
            import rclpy
            print("Detected ROS 2")
            ROSMessageImporter._import_ros2_messages()
        except ImportError:
            try:
                import rospy
                print("Detected ROS 1")
                ROSMessageImporter._import_ros1_messages()
            except ImportError:
                raise RuntimeError("Neither ROS 1 nor ROS 2 is detected. Ensure ROS is sourced.")

    @staticmethod
    def _import_ros2_messages():
        import ament_index_python.packages

        all_packages = ament_index_python.packages.get_packages_with_prefixes().keys()
        msg_packages = [pkg for pkg in all_packages if pkg.endswith('_msgs') or pkg.endswith('msgs')]
        
        print(f"Loading {len(msg_packages)} ROS 2 message packages...")
        
        total_loaded = 0
        for package in msg_packages:
            try:
                module = importlib.import_module(f"{package}.msg")
                package_count = 0
                
                for attr in dir(module):
                    if not attr.startswith('_'):
                        cls = getattr(module, attr)
                        if hasattr(cls, "__slots__"):
                            ROSMessageImporter._msg_classes[f"{package}/{attr}"] = cls
                            package_count += 1
                
                if package_count > 0:
                    print(f"✅ Loaded {package_count} messages from {package}")
                    total_loaded += package_count
                else:
                    print(f"⚠️ No message classes found in {package}")
                    
            except ImportError:
                print(f"⚠️ Package {package} has no msg module, skipping.")
            except Exception as e:
                print(f"❌ Error loading {package}: {e}")
        
        print(f"Total messages loaded: {total_loaded}")

    @staticmethod
    def _import_ros1_messages():
        import rosmsg
        import rospkg

        rospack = rospkg.RosPack()
        packages = rospack.list()
        print(f"Loading {len(packages)} ROS 1 packages...")

        all_messages = []
        for package in packages:
            try:
                msgs = rosmsg.list_msgs(package)
                all_messages.extend(msgs)
            except rospkg.common.ResourceNotFound:
                print(f"⚠️ Package {package} not found, skipping.")
        
        if not all_messages:
            print("❌ No messages found. Ensure ROS is sourced.")
            return

        print(f"Loading {len(all_messages)} message types...")

        for msg in all_messages:
            try:
                package, msg_type = msg.split("/")
                module = importlib.import_module(f"{package}.msg")
                cls = getattr(module, msg_type, None)
                if cls:
                    ROSMessageImporter._msg_classes[msg] = cls
                    print(f"✅ Loaded {msg}")
                else:
                    print(f"⚠️ Failed to load {msg}")
            except (ModuleNotFoundError, AttributeError) as e:
                print(f"❌ Error loading {msg}: {e}")

    @staticmethod
    def get_class(datatype):
        if datatype in ROSMessageImporter._msg_classes:
            return ROSMessageImporter._msg_classes[datatype]
        
        normalized = datatype.replace("/msg/", "/")
        return ROSMessageImporter._msg_classes.get(normalized)

    @staticmethod
    def list_all_loaded():
        """Display all loaded message types."""
        print(f"\nAll loaded message types ({len(ROSMessageImporter._msg_classes)}):")
        for msg_type in sorted(ROSMessageImporter._msg_classes.keys()):
            print(f"  {msg_type}")

def main():
    ROSMessageImporter.import_all_messages()
    
    ROSMessageImporter.list_all_loaded()
    
    print("\nTesting specific message types:")
    test_msgs = ["std_msgs/String", "geometry_msgs/Twist", "sensor_msgs/Image", 
                 "sensor_msgs/msg/Imu", "std_msgs/msg/String"]

    for msg in test_msgs:
        msg_class = ROSMessageImporter.get_class(msg)
        if msg_class:
            print(f"✅ Successfully loaded {msg}: {msg_class}")
        else:
            print(f"❌ Failed to load {msg}")

if __name__ == "__main__":
    main()
