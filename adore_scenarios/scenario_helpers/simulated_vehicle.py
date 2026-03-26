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

from typing import Any, Dict, List, Optional, Tuple

from launch import Action
from launch_ros.actions import ComposableNodeContainer, Node
from launch_ros.descriptions import ComposableNode

from scenario_helpers.simulation_planner_params import planner_params
from scenario_helpers.simulation_controller_params import simulation_pid_params

# Example only
SIMULATED_V2X_TOPIC_PARAMETERS: Dict[str, str] = {
    "topic_infrastructure_participants": "v2x_planned_traffic",
}
STANDARD_TOPIC_PARAMETERS: Dict[str, str] = {
    "topic_infrastructure_participants": "/planned_traffic",
}


def with_topic_params(
    *param_dicts: Dict[str, Any],
    topic_params: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """Return a list of parameter dictionaries ending with topic parameters.

    Enforces topic_params as keyword-only for clarity.
    """
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
) -> List[ComposableNode]:
    """Create composable components for the simulated vehicle stack."""
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
                {"controller_settings_keys": list(
                    simulation_pid_params.keys())},
                {"controller_settings_values": list(
                    simulation_pid_params.values())},
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
) -> List[Action]:
    """Create standalone ROS 2 nodes for the simulated vehicle stack."""
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
                {"planner_settings_keys": list(planner_params.keys())},
                {"planner_settings_values": list(planner_params.values())},
                {"vehicle_model_file": model_file},
                {"v2x_id": v2x_id},
                
                # Parameters for path shift behavior (example values, adjust as needed)
                {"path_shift.min_object_ahead": 4.0},
                {"path_shift.max_object_ahead": 35.0},
                {"path_shift.max_object_speed": 0.5},
                {"path_shift.static_clearance": 0.6},
                {"path_shift.front_clearance": 1.0},
                {"path_shift.rear_clearance": 1.0},
                {"path_shift.approach_length": 15.0},
                {"path_shift.return_length": 6.0},
                {"path_shift.target_speed": 3.0},
                {"path_shift.lookahead_length": 50.0},
                {"path_shift.max_shift_left": 2.0},
                {"path_shift.route_overlap_slack": 0.5},
                {"path_shift.oncoming_front_buffer": 20.0},
                {"path_shift.oncoming_rear_buffer": 5.0},
                {"path_shift.min_oncoming_angle_diff": 2.0},
                
                {"path_shift.prediction_time_step": 0.1},
                {"path_shift.prediction_time_horizon": 6.0},
                {"path_shift.min_ego_prediction_speed": 1.5},
                {"path_shift.min_oncoming_route_speed": 0.5},
                {"path_shift.oncoming_vehicle_s_margin": 1.0},
                {"path_shift.max_stationary_conflict_route_speed": 0.2},
                {"path_shift.static_oncoming_s_margin": 1.0},
                {"path_shift.ego_vehicle_s_margin": 1.0},

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
                {"controller_settings_keys": list(
                    simulation_pid_params.keys())},
                {"controller_settings_values": list(
                    simulation_pid_params.values())},
                {"vehicle_model_file": model_file},
                topic_params=topic_params,
            ),
        ),
    ]


def create_simulated_vehicle_nodes(
    namespace: str,
    start_pose: Tuple[float, float, float],
    goal_position: Tuple[float, float],
    vehicle_id: int,
    map_file: str,
    model_file: str,
    debug: bool = False,
    controller: int = 1,
    controllable: bool = True,
    v2x_id: int = 0,
    simulated_v2x_mode: bool = False,
    request_assistance_polygon: Optional[List[float]] = None,
    composable: bool = False,
    local_map_size: float = 100.0,
) -> List[Action]:
    """Create simulated vehicle nodes or components for ROS 2 launch.

    Returns a list of launch Actions (either a container or individual Nodes).
    """
    x, y, psi = start_pose
    goal_x, goal_y = goal_position

    if request_assistance_polygon is None:
        request_assistance_polygon = [0.0, 0.0]

    topic_params = (
        SIMULATED_V2X_TOPIC_PARAMETERS if simulated_v2x_mode else STANDARD_TOPIC_PARAMETERS
    )

    if composable:
        components = _build_composable_components(
            namespace=namespace,
            x=x,
            y=y,
            psi=psi,
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

        )

        container = ComposableNodeContainer(
            name="sim_container",
            namespace="",
            package="rclcpp_components",
            executable="component_container_mt",
            composable_node_descriptions=components,
            output="screen",
        )
        return [container]

    # Standalone nodes
    return _build_standalone_nodes(
        namespace=namespace,
        x=x,
        y=y,
        psi=psi,
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

    )
