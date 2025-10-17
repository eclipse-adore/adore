# ********************************************************************************
# Copyright (c) 2025 Contributors to the Eclipse Foundation
#
# See the NOTICE file(s) distributed with this work for additional
# information regarding copyright ownership.
#
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# https://www.eclipse.org/legal/epl-2.0
#
# SPDX-License-Identifier: EPL-2.0
# ********************************************************************************

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
            executable='foxglove_bridge',
            name='foxglove_bridge',
            output='screen',
            emulate_tty=True,
            parameters=[
                {'port': port},
                {'send_buffer_limit': send_buffer_limit},
                {'use_compression': False}  # Try disabling compression
            ],
            arguments=['--ros-args', '--log-level', 'info'],
            respawn=True,
            respawn_delay=2.0
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
