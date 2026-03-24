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

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Tuple, Union

from launch import Action
from launch_ros.actions import ComposableNodeContainer, Node
from launch_ros.descriptions import ComposableNode

from scenario_helpers.simulation_planner_params import planner_params
from scenario_helpers.simulation_controller_params import simulation_pid_params

SIMULATED_V2X_TOPIC_PARAMETERS: Dict[str, str] = {
    "topic_infrastructure_participants": "v2x_planned_traffic",
}
STANDARD_TOPIC_PARAMETERS: Dict[str, str] = {
    "topic_infrastructure_participants": "/planned_traffic",
}


class Position:
    def __init__(self, lat_long=None, utm=None, psi=0.0):
        self.psi = psi
        if lat_long is not None and utm is not None:
            raise ValueError("Cannot specify both lat_long and utm coordinates")
        elif lat_long is not None:
            self.lat, self.long = lat_long
            self.utm_x, self.utm_y, self.utm_zone, self.utm_hemisphere = self._lat_long_to_utm(self.lat, self.long)
        elif utm is not None:
            if len(utm) == 4:
                self.utm_x, self.utm_y, self.utm_zone, self.utm_hemisphere = utm
            else:
                raise ValueError("UTM coordinates must be (x, y, zone, hemisphere)")
            self.lat, self.long = self._utm_to_lat_long(self.utm_x, self.utm_y, self.utm_zone, self.utm_hemisphere)
        else:
            raise ValueError("Must specify either lat_long or utm coordinates")

    def _lat_long_to_utm(self, lat, long):
        from pyproj import Transformer
        zone = int(math.floor((long + 180) / 6) + 1)
        hemisphere = 'N' if lat >= 0 else 'S'
        epsg = 32600 + zone if hemisphere == 'N' else 32700 + zone
        transformer = Transformer.from_crs("epsg:4326", f"epsg:{epsg}", always_xy=True)
        utm_x, utm_y = transformer.transform(long, lat)
        return utm_x, utm_y, zone, hemisphere

    def _utm_to_lat_long(self, utm_x, utm_y, zone, hemisphere):
        from pyproj import Transformer
        epsg = 32600 + zone if hemisphere == 'N' else 32700 + zone
        transformer = Transformer.from_crs(f"epsg:{epsg}", "epsg:4326", always_xy=True)
        long, lat = transformer.transform(utm_x, utm_y)
        return lat, long

    def get_utm_coordinates(self) -> Tuple[float, float, float]:
        return self.utm_x, self.utm_y, self.psi

    def get_lat_long_coordinates(self) -> Tuple[float, float, float]:
        return self.lat, self.long, self.psi


def with_topic_params(
    *param_dicts: Dict[str, Any],
    topic_params: Dict[str, Any],
) -> List[Dict[str, Any]]:
    return list(param_dicts) + [topic_params]


def _build_composable_components(
    *,
    namespace: str,
    x: float,
    y: float,
    psi: float,
    controllable: bool,
    vehicle_id: int,
    v2x_id: int,
    map_file: str,
    model_file: str,
    goal_x: float,
    goal_y: float,
    local_map_size: float,
    request_assistance_polygon: List[float],
    topic_params: Dict[str, Any],
    debug: bool,
    controller: int,
    optinlc_route_following: bool,
) -> List[ComposableNode]:
    return [
        ComposableNode(
            package="simulated_vehicle",
            plugin="adore::simulated_vehicle::SimulatedVehicleNode",
            name="simulated_vehicle",
            namespace=namespace,
            parameters=with_topic_params(
                {"set_start_position_x": x},
                {"set_start_position_y": y},
                {"set_start_psi": psi},
                {"controllable": controllable},
                {"vehicle_id": vehicle_id},
                {"v2x_id": v2x_id},
                {"vehicle_model_file": model_file},
                topic_params=topic_params,
            ),
        ),
        ComposableNode(
            package="mission_control",
            plugin="adore::MissionControlNode",
            name="mission_control",
            namespace=namespace,
            parameters=with_topic_params(
                {"map file": map_file},  # kept literal key as in original
                {"goal_position_x": goal_x},
                {"goal_position_y": goal_y},
                {"local_map_size": local_map_size},
                {"request_assistance_polygon": request_assistance_polygon},
                topic_params=topic_params,
            ),
        ),
        ComposableNode(
            package="decision_maker",
            plugin="adore::DecisionMaker",
            name="decision_maker",
            namespace=namespace,
            parameters=with_topic_params(
                {"debug_mode_active": debug},
                {"optinlc_route_following": optinlc_route_following},
                {"planner_settings_keys": list(planner_params.keys())},
                {"planner_settings_values": list(planner_params.values())},
                {"vehicle_model_file": model_file},
                {"v2x_id": v2x_id},
                topic_params=topic_params,
            ),
        ),
        ComposableNode(
            package="trajectory_tracker",
            plugin="adore::TrajectoryTrackerNode",
            name="trajectory_tracker",
            namespace=namespace,
            parameters=with_topic_params(
                {"set_controller": controller},
                {"controller_settings_keys": list(simulation_pid_params.keys())},
                {"controller_settings_values": list(simulation_pid_params.values())},
                {"vehicle_model_file": model_file},
                topic_params=topic_params,
            ),
        ),
    ]


def _build_standalone_nodes(
    *,
    namespace: str,
    x: float,
    y: float,
    psi: float,
    controllable: bool,
    vehicle_id: int,
    v2x_id: int,
    map_file: str,
    model_file: str,
    goal_x: float,
    goal_y: float,
    local_map_size: float,
    request_assistance_polygon: List[float],
    topic_params: Dict[str, Any],
    debug: bool,
    controller: int,
    optinlc_route_following: bool,
) -> List[Action]:
    return [
        Node(
            package="simulated_vehicle",
            executable="simulated_vehicle",
            name="simulated_vehicle",
            namespace=namespace,
            parameters=with_topic_params(
                {"set_start_position_x": x},
                {"set_start_position_y": y},
                {"set_start_psi": psi},
                {"controllable": controllable},
                {"vehicle_id": vehicle_id},
                {"v2x_id": v2x_id},
                {"vehicle_model_file": model_file},
                topic_params=topic_params,
            ),
        ),
        Node(
            package="mission_control",
            executable="mission_control",
            name="mission_control",
            namespace=namespace,
            parameters=with_topic_params(
                {"map file": map_file},  # kept literal key as in original
                {"goal_position_x": goal_x},
                {"goal_position_y": goal_y},
                {"local_map_size": local_map_size},
                {"request_assistance_polygon": request_assistance_polygon},
                topic_params=topic_params,
            ),
        ),
        Node(
            package="decision_maker",
            executable="decision_maker",
            name="decision_maker",
            namespace=namespace,
            parameters=with_topic_params(
                {"debug_mode_active": debug},
                {"optinlc_route_following": optinlc_route_following},
                {"planner_settings_keys": list(planner_params.keys())},
                {"planner_settings_values": list(planner_params.values())},
                {"vehicle_model_file": model_file},
                {"v2x_id": v2x_id},
                topic_params=topic_params,
            ),
        ),
        Node(
            package="trajectory_tracker",
            executable="trajectory_tracker",
            name="trajectory_tracker",
            namespace=namespace,
            parameters=with_topic_params(
                {"set_controller": controller},
                {"controller_settings_keys": list(simulation_pid_params.keys())},
                {"controller_settings_values": list(simulation_pid_params.values())},
                {"vehicle_model_file": model_file},
                topic_params=topic_params,
            ),
        ),
    ]


def create_simulated_vehicle_nodes(
    namespace: str,
    goal_position: Union[Position, Tuple[float, float]],
    start_position: Optional[Position] = None,
    start_pose: Optional[Tuple[float, float, float]] = None,
    vehicle_id: int = 0,
    map_file: str = "",
    model_file: str = "",
    debug: bool = False,
    controller: int = 1,
    controllable: bool = True,
    v2x_id: int = 0,
    optinlc_route_following: bool = False,
    simulated_v2x_mode: bool = False,
    request_assistance_polygon: Optional[List[float]] = None,
    composable: bool = False,
    local_map_size: float = 100.0,
) -> List[Action]:
    if start_position is not None:
        x, y, psi = start_position.get_utm_coordinates()
    elif start_pose is not None:
        x, y, psi = start_pose
    else:
        raise ValueError("Must provide either start_position (Position) or start_pose (tuple)")

    if isinstance(goal_position, Position):
        goal_x, goal_y, _ = goal_position.get_utm_coordinates()
    else:
        goal_x, goal_y = goal_position

    if request_assistance_polygon is None:
        request_assistance_polygon = [0.0, 0.0]

    topic_params = (
        SIMULATED_V2X_TOPIC_PARAMETERS if simulated_v2x_mode else STANDARD_TOPIC_PARAMETERS
    )

    builder_kwargs = dict(
        namespace=namespace,
        x=x, y=y, psi=psi,
        controllable=controllable,
        vehicle_id=vehicle_id,
        v2x_id=v2x_id,
        map_file=map_file,
        model_file=model_file,
        goal_x=goal_x,
        goal_y=goal_y,
        local_map_size=local_map_size,
        request_assistance_polygon=request_assistance_polygon,
        topic_params=topic_params,
        debug=debug,
        controller=controller,
        optinlc_route_following=optinlc_route_following,
    )

    if composable:
        components = _build_composable_components(**builder_kwargs)
        return [ComposableNodeContainer(
            name="sim_container",
            namespace="",
            package="rclcpp_components",
            executable="component_container_mt",
            composable_node_descriptions=components,
            output="screen",
        )]

    return _build_standalone_nodes(**builder_kwargs)
