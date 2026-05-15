from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from ament_index_python.packages import get_package_share_directory
import os

def generate_launch_description():
    config = os.path.join(get_package_share_directory('zenoh_message_bridge'), 'config', 'bridge_config.yaml')
    return LaunchDescription([
        DeclareLaunchArgument('zenoh_router', default_value='tcp/localhost:7447'),
        Node(
            package='zenoh_message_bridge',
            executable='bridge_node',
            parameters=[{
                'config_path': config,
                'zenoh_router': LaunchConfiguration('zenoh_router'),
            }]
        )
    ])
