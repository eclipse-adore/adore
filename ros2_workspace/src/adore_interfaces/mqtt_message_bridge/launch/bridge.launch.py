from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
import os

def generate_launch_description():
    default_config = os.path.join(
        get_package_share_directory('mqtt_message_bridge'), 'config', 'bridge_config.yaml')
    config_path = LaunchConfiguration('config_path')
    return LaunchDescription([
        DeclareLaunchArgument('config_path', default_value=default_config),
        Node(
            package='mqtt_message_bridge',
            executable='bridge_node',
            parameters=[{'config_path': config_path}],
        ),
    ])
