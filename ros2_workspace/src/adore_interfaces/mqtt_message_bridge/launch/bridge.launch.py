from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from ament_index_python.packages import get_package_share_directory
import os

def generate_launch_description():
    config = os.path.join(get_package_share_directory('mqtt_message_bridge'), 'config', 'bridge_config.yaml')
    return LaunchDescription([
        DeclareLaunchArgument('mqtt_broker', default_value='localhost'),
        DeclareLaunchArgument('mqtt_port', default_value='1883'),
        Node(
            package='mqtt_message_bridge',
            executable='bridge_node',
            parameters=[{
                'config_path': config,
                'mqtt_broker': LaunchConfiguration('mqtt_broker'),
                'mqtt_port': LaunchConfiguration('mqtt_port'),
            }]
        )
    ])
