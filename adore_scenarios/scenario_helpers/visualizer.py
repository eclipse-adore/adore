from launch_ros.actions import Node
import os

def create_visualization_nodes(whitelist, asset_folder, ns="ego_vehicle", use_center_ego=True, port=8765, send_buffer_limit=500000000):
    """
    Returns a list of nodes for visualization (foxglove bridge and visualizer).

    Parameters:
        whitelist (list[str]): List of topic namespace prefixes to visualize.
        asset_folder (str): Path to folder containing map image assets.
        use_center_ego (bool): Whether the ego vehicle should be used as map center.
        port (int): Port for Foxglove Bridge.
        send_buffer_limit (int): Buffer limit for Foxglove Bridge.

    Returns:
        list[Node]: Launchable ROS 2 Node actions.
    """
    return [
        Node(
            package='foxglove_bridge',
            namespace='global',
            executable='foxglove_bridge',
            name='foxglove_bridge',
            output='screen',
            parameters=[
                {'port': port},
                {'send_buffer_limit': send_buffer_limit}
            ],
        ),
        Node(
            package='visualizer',
            namespace=ns,
            executable='visualizer',
            name='visualizer',
            parameters=[
                {"asset folder": asset_folder},
                {"whitelist": whitelist},
                {"center_ego_vehicle": use_center_ego}
            ]
        )
    ]
