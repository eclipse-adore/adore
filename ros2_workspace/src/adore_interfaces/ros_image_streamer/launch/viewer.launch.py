from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from ament_index_python.packages import get_package_share_directory
import os


def generate_launch_description():
    config = os.path.join(
        get_package_share_directory('ros_image_streamer'),
        'config', 'viewer_config.yaml'
    )

    return LaunchDescription([
        DeclareLaunchArgument('config_path', default_value=config),

        Node(
            package='ros_image_streamer',
            executable='viewer_node',
            name='viewer_node',
            parameters=[{'config_path': LaunchConfiguration('config_path')}],
            output='screen',
        ),
    ])
