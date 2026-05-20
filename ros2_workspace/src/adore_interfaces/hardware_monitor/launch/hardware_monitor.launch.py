from launch import LaunchDescription
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
import os


def generate_launch_description():
    config = os.path.join(
        get_package_share_directory('hardware_monitor'),
        'config',
        'hardware_monitor.yaml',
    )
    return LaunchDescription([
        Node(
            package='hardware_monitor',
            executable='hardware_discovery_node',
            name='hardware_discovery_node',
            parameters=[config],
            output='screen',
        ),
        Node(
            package='hardware_monitor',
            executable='hardware_status_node',
            name='hardware_status_node',
            parameters=[config],
            output='screen',
        ),
    ])
