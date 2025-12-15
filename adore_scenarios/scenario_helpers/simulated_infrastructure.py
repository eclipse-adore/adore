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

# example only
simulated_v2x_topic_parameters = {
    "planned_traffic_out_topic": "v2x_planned_traffic",
    "traffic_participant_in_topic": "v2x_traffic_participant",
}
topic_parameters = {
    "planned_traffic_out_topic": "/planned_traffic",
    "traffic_participant_in_topic": "traffic_participant",
}


def with_topic_params(*param_dicts: dict, topic_params) -> list[dict]:

    return list(param_dicts) + [topic_params]


def create_infrastructure_nodes(position: tuple[float, float],
                                polygon: list[float],
                                map_file: str,
                                simulated_v2x_mode: bool = False,
                                debug=True) -> list[Node]:
    x, y = position
    topic_params = topic_parameters
    if simulated_v2x_mode:
        topic_params = simulated_v2x_topic_parameters

    return [
        Node(
            package='decision_maker_infrastructure',
            namespace='infrastructure',
            executable='decision_maker_infrastructure',
            name='decision_maker_infrastructure',
            parameters=with_topic_params(
                {"map file": map_file},
                {"infrastructure_position_x": x},
                {"infrastructure_position_y": y},
                {"debug": debug},
                {"validity_polygon": polygon},
                {"multi_agent_PID_settings_keys": ["preview_distance", "k_yaw", "k_distance"]
                 },
                {"multi_agent_PID_settings_values": [4.5, 2.0, 1.0]
                 }, topic_params=topic_params
            ),
        )
    ]
