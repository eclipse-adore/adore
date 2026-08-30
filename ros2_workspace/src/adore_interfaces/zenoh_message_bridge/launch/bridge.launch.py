from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch.substitutions import LaunchConfiguration
from ament_index_python.packages import get_package_share_directory
import os

def default_config_path():
    pkg_share = get_package_share_directory('zenoh_message_bridge')
    return os.path.join(pkg_share, 'config', 'bridge_config.yaml')

def bridge_node(context, *args, **kwargs):
    paths = LaunchConfiguration('config_paths').perform(context)
    config_paths = [p.strip() for p in paths.split(',') if p.strip()]

    return [
        Node(
            package='zenoh_message_bridge',
            executable='bridge_node',
            parameters=[{
                'config_path': LaunchConfiguration('config_path'),
                'config_paths': config_paths or [''],
                'zenoh_config_path': LaunchConfiguration('zenoh_config_path'),
                'zenoh_router': LaunchConfiguration('zenoh_router'),
            }]
        )
    ]

def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument('config_path', default_value=default_config_path()),
        DeclareLaunchArgument('config_paths', default_value='',
                              description='Comma separated config files, merged in order. Takes precedence over config_path.'),
        DeclareLaunchArgument('zenoh_router', default_value='tcp/localhost:7447'),
        DeclareLaunchArgument('zenoh_config_path', default_value=''),
        OpaqueFunction(function=bridge_node),
    ])
