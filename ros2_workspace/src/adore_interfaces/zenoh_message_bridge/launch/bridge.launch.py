from launch import LaunchDescription
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
import os

def generate_launch_description():
    config = os.path.join(get_package_share_directory('zenoh_message_bridge'), 'config', 'bridge_config.yaml')
    return LaunchDescription([
        Node(
            package='zenoh_message_bridge',
            executable='bridge_node',
            parameters=[{'config_path': config}]
        )
    ])
