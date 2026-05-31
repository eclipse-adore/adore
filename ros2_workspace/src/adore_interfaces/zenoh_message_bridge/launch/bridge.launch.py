from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from ament_index_python.packages import get_package_share_directory
import os

def generate_launch_description():
    pkg_share = get_package_share_directory('zenoh_message_bridge')
    bridge_config = os.path.join(pkg_share, 'config', 'bridge_config.yaml')

    return LaunchDescription([
        DeclareLaunchArgument('zenoh_router', default_value='tcp/localhost:7447'),
        DeclareLaunchArgument('zenoh_config_path', default_value=''),
        Node(
            package='zenoh_message_bridge',
            executable='bridge_node',
            parameters=[{
                'config_path': bridge_config,
                'zenoh_config_path': LaunchConfiguration('zenoh_config_path'),
                'zenoh_router': LaunchConfiguration('zenoh_router'),
            }]
        )
    ])
