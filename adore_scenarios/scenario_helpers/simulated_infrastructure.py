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

def create_infrastructure_nodes(position: tuple[float, float],
                                 polygon: list[float],
                                 map_file: str) -> list[Node]:
    x, y = position

    return [
        Node(
            package='simulated_infrastructure',
            namespace='infrastructure',
            executable='simulated_infrastructure',
            name='simulated_infrastructure',
            parameters=[
                {"infrastructure_position_x": x},
                {"infrastructure_position_y": y},
                {"validity_polygon": polygon}
            ]
        ),
        Node(
            package='decision_maker_infrastructure',
            namespace='infrastructure',
            executable='decision_maker_infrastructure',
            name='decision_maker_infrastructure',
            parameters=[
                {"map file": map_file},
                {"infrastructure_position_x": x},
                {"infrastructure_position_y": y},
                {"debug_mode_active": False},
                {"validity_polygon": polygon},
                {"multi_agent_PID_settings_keys": ["preview_distance", "k_yaw", "k_distance"]
                },
                {"multi_agent_PID_settings_values": [4.5, 2.0, 1.0]
                }
            ]
        )
    ]
