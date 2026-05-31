from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from ament_index_python.packages import get_package_share_directory
import os


def generate_launch_description():
    pkg_share = get_package_share_directory('ros_image_streamer')
    streamer_config = os.path.join(pkg_share, 'config', 'streamer_config.yaml')
    viewer_config   = os.path.join(pkg_share, 'config', 'viewer_config.yaml')

    return LaunchDescription([
        DeclareLaunchArgument('streamer_config_path', default_value=streamer_config),
        DeclareLaunchArgument('viewer_config_path',   default_value=viewer_config),

        Node(
            package='ros_image_streamer',
            executable='streaming_node',
            name='streaming_node',
            parameters=[{'config_path': LaunchConfiguration('streamer_config_path')}],
            output='screen',
        ),

        Node(
            package='ros_image_streamer',
            executable='viewer_node',
            name='viewer_node',
            parameters=[{'config_path': LaunchConfiguration('viewer_config_path')}],
            output='screen',
        ),
    ])
