from launch_ros.actions import Node, ComposableNodeContainer
from launch_ros.descriptions import ComposableNode
import os
import sys
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

from scenario_helpers.simulation_planner_params import planner_params
from scenario_helpers.simulation_controller_params import simulation_pid_params


def create_simulated_vehicle_nodes(
    namespace: str,
    start_pose: tuple[float, float, float],
    goal_position: tuple[float, float],
    vehicle_id: int,
    map_file: str,
    model_file: str,
    debug: bool = False,
    optinlc_route_following: bool = False,
    controller: int = 1,
    controllable: bool = True,
    v2x_id: int = 0,
    request_assistance_polygon: list[float] = [0.0, 0.0],
    shape: tuple[float, float, float] = (4.0, 2.0, 2.0),
    composable: bool = False,
    local_map_size: float = 50.0,
):
    x, y, psi = start_pose
    goal_x, goal_y = goal_position

    if composable:
        components = [
            # ComposableNode(
            #     package="adore_v2x_interface",
            #     plugin="adore::EgoV2XInterface",
            #     name="adore_v2x_interface",
            #     namespace=namespace,
            #     parameters=[{"ego_v2x_id": 222}],
            # ),
            ComposableNode(
                package="simulated_vehicle",
                plugin="adore::simulated_vehicle::SimulatedVehicleNode",
                name="simulated_vehicle",
                namespace=namespace,
                parameters=[
                    {"set_start_position_x": x},
                    {"set_start_position_y": y},
                    {"set_start_psi": psi},
                    {"controllable": controllable},
                    {"vehicle_id": vehicle_id},
                    {"v2x_id": v2x_id},
                    {"vehicle_model_file": model_file},
                    {"set_shape": list(shape)},
                ],
            ),
            ComposableNode(
                package="mission_control",
                plugin="adore::MissionControlNode",
                name="mission_control",
                namespace=namespace,
                parameters=[
                    {"map file": map_file},
                    {"goal_position_x": goal_x},
                    {"goal_position_y": goal_y},
                    {"local_map_size": local_map_size}
                ],
            ),
            ComposableNode(
                package="decision_maker",
                plugin="adore::DecisionMaker",
                name="decision_maker",
                namespace=namespace,
                parameters=[
                    {"debug_mode_active": debug},
                    {"optinlc_route_following": optinlc_route_following},
                    {"planner_settings_keys": list(planner_params.keys())},
                    {"planner_settings_values": list(planner_params.values())},
                    {"request_assistance_polygon": request_assistance_polygon},
                    {"vehicle_model_file": model_file},
                ],
            ),
            ComposableNode(
                package="trajectory_tracker",
                plugin="adore::TrajectoryTrackerNode",
                name="trajectory_tracker",
                namespace=namespace,
                parameters=[
                    {"set_controller": controller},
                    {"controller_settings_keys": list(simulation_pid_params.keys())},
                    {"controller_settings_values": list(simulation_pid_params.values())},
                    {"vehicle_model_file": model_file},
                ],
            ),
        ]

        container = ComposableNodeContainer(
            name='sim_container',
            namespace='',
            package='rclcpp_components',
            executable='component_container_mt',
            composable_node_descriptions=components,
            output='screen',
        )
        return [container]
    else:
        return [
            # Node(
            #     package="adore_v2x_interface",
            #     executable="ego_v2x_interface_node",
            #     name="adore_v2x_interface",
            #     namespace=namespace,
            #     parameters=[{"ego_v2x_id": 222}],
            # ),
            Node(
                package="simulated_vehicle",
                executable="simulated_vehicle",
                name="simulated_vehicle",
                namespace=namespace,
                parameters=[
                    {"set_start_position_x": x},
                    {"set_start_position_y": y},
                    {"set_start_psi": psi},
                    {"controllable": controllable},
                    {"vehicle_id": vehicle_id},
                    {"v2x_id": v2x_id},
                    {"vehicle_model_file": model_file},
                    {"set_shape": list(shape)},
                ],
            ),
            Node(
                package="mission_control",
                executable="mission_control",
                name="mission_control",
                namespace=namespace,
                parameters=[
                    {"map file": map_file},
                    {"goal_position_x": goal_x},
                    {"goal_position_y": goal_y},
                    {"local_map_size": local_map_size}

                ],
            ),
            Node(
                package="decision_maker",
                executable="decision_maker",
                name="decision_maker",
                namespace=namespace,
                parameters=[
                    {"debug_mode_active": debug},
                    {"optinlc_route_following": optinlc_route_following},
                    {"planner_settings_keys": list(planner_params.keys())},
                    {"planner_settings_values": list(planner_params.values())},
                    {"request_assistance_polygon": request_assistance_polygon},
                    {"vehicle_model_file": model_file},
                ],
            ),
            Node(
                package="trajectory_tracker",
                executable="trajectory_tracker",
                name="trajectory_tracker",
                namespace=namespace,
                parameters=[
                    {"set_controller": controller},
                    {"controller_settings_keys": list(simulation_pid_params.keys())},
                    {"controller_settings_values": list(simulation_pid_params.values())},
                    {"vehicle_model_file": model_file},
                ],
            ),
        ]
