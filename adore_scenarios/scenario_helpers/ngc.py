from launch_ros.actions import Node
import os
from scenario_helpers.simulation_planner_params import planner_params
from scenario_helpers.ngc_controller_params import ngc_pid_params

def create_ngc_nodes(
    namespace: str,
    goal_position: tuple[float, float],
    map_file: str,
    debug: bool = False,
    optinlc_route_following: bool = True,
    controller: int = 1,
    custom_start_pose: tuple[float, float, float] | None = None,
    request_assistance_polygon: list[float] = [0.0,0.0]) -> list[Node]:

    launch_file_dir = os.path.dirname(os.path.realpath(__file__))
    vehicle_param = os.path.abspath(os.path.join(launch_file_dir, "../assets/vehicle_params/"))
    model_file = vehicle_param + "/NGC.json"
    x, y, psi = custom_start_pose
    goal_x, goal_y = goal_position

    nodes = [
        Node(
            package='adore_bob_interface',
            namespace='ego_vehicle',
            executable='adore_bob_interface',
            name='adore_bob_interface',
            parameters=[
                {"publish_traffic_participants": True},
                {"vehicle_name": "ngc"},
            ],
            #output={'both': 'log'},
        ),
        Node(
           package='adore_v2x_interface',
           namespace='ego_vehicle',
           executable='ego_v2x_interface_node',
           name='adore_v2x_interface',
           parameters=[
                {"ego_v2x_id": 222},
            ],

        ),
        Node(
            package='adore_vehicle_interface',
            namespace='ego_vehicle',
            executable='vehicle_udp_gateway_node',
            name='vehicle_udp_gateway_node',
            parameters=[
                {"VehicleID":"NGC"},
            ],
            shell=False,
            output="screen",
            prefix=['xterm -e'],
        ),
        Node(
            package="mission_control",
            namespace=namespace,
            executable="mission_control",
            name="mission_control",
            parameters=[
                {"map file": map_file},
                {"goal_position_x": goal_x},
                {"goal_position_y": goal_y},
            ],
        ),
        Node(
            package="decision_maker",
            namespace=namespace,
            executable="decision_maker",
            name="decision_maker",
            parameters=[
                {"debug_mode_active": debug},
                {"optinlc_route_following": optinlc_route_following},
                {"planner_settings_keys": list(planner_params.keys())},
                {"planner_settings_values": list(planner_params.values())},
                {"request_assistance_polygon": request_assistance_polygon},
                {"vehicle_model_file": model_file}
            ],
            # output={"both": "log"},
        ),
        Node(
            package="trajectory_tracker",
            namespace=namespace,
            executable="trajectory_tracker_node",
            name="trajectory_tracker",
            parameters=[
                {"set_controller": controller},
                {"controller_settings_keys": list(ngc_pid_params.keys())},
                {"controller_settings_values": list(ngc_pid_params.values())},
                {"vehicle_model_file": model_file},
            ],
        ),
    ]

    return nodes
