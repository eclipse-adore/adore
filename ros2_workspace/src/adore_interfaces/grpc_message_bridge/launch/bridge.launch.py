from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    pkg = FindPackageShare('grpc_message_bridge')

    return LaunchDescription([
        DeclareLaunchArgument('config_path',
            default_value=PathJoinSubstitution([pkg, 'config', 'bridge_config.yaml'])),
        DeclareLaunchArgument('grpc_host', default_value='0.0.0.0'),
        DeclareLaunchArgument('grpc_port', default_value='50051'),

        Node(
            package    = 'grpc_message_bridge',
            executable = 'bridge_node',
            name       = 'grpc_bridge_node',
            parameters = [{
                'config_path': LaunchConfiguration('config_path'),
                'grpc_host':   LaunchConfiguration('grpc_host'),
                'grpc_port':   LaunchConfiguration('grpc_port'),
            }],
            output = 'screen',
        ),
    ])
