from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument('topic',       default_value='/camera/image_raw'),
        DeclareLaunchArgument('window_name', default_value='ROS Image Viewer'),

        Node(
            package='ros_image_streamer',
            executable='viewer_node',
            name='viewer_node',
            parameters=[{
                'topic':       LaunchConfiguration('topic'),
                'window_name': LaunchConfiguration('window_name'),
            }],
            output='screen',
        ),
    ])
