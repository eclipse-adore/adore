from launch_ros.actions import Node
import os


def create_visualization_nodes(whitelist, asset_folder, visualization_offset, ns="visualizer", port=8765, send_buffer_limit=500000000):
    """
    Returns a list of nodes for visualization (foxglove bridge and visualizer).

    Parameters:
        whitelist (list[str]): List of topic namespace prefixes to visualize.
        asset_folder (str): Path to folder containing map image assets.
        port (int): Port for Foxglove Bridge.
        send_buffer_limit (int): Buffer limit for Foxglove Bridge.

    Returns:
        list[Node]: Launchable ROS 2 Node actions.
    """
    return [
        Node(
            package='rosapi',
            executable='rosapi_node',
            name='rosapi',
            output='screen'
        ),
        Node(
            package='rosbridge_server',
            executable='rosbridge_websocket',
            name='rosbridge_websocket',
            output='screen',
            parameters=[
                {'port': port},
                {'address': '0.0.0.0'},
                {'use_compression': False},
                {'fragment_timeout': 600},
                {'delay_between_messages': 0},
                {'max_message_size': 10000000},
                {'unregister_timeout': 10.0}
            ]
        ),
        Node(
            package='visualizer',
            namespace=ns,
            executable='visualizer',
            name='visualizer',
            parameters=[
                {"asset folder": asset_folder},
                {"whitelist": whitelist},
                {"visualization_offset_x": visualization_offset[0]},
                {"visualization_offset_y": visualization_offset[1]},
            ]
        )
    ]
