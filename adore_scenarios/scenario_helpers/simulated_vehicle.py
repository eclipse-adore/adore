from launch_ros.actions import Node, ComposableNodeContainer
from launch_ros.descriptions import ComposableNode
import os
import sys
import math
import pyproj

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

from scenario_helpers.simulation_planner_params import planner_params
from scenario_helpers.simulation_controller_params import simulation_pid_params


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
        zone = int(math.floor((long + 180) / 6) + 1)
        hemisphere = 'N' if lat >= 0 else 'S'
        
        utm_proj = pyproj.Proj(proj='utm', zone=zone, datum='WGS84')
        wgs84_proj = pyproj.Proj(proj='latlong', datum='WGS84')
        
        utm_x, utm_y = pyproj.transform(wgs84_proj, utm_proj, long, lat)
        
        return utm_x, utm_y, zone, hemisphere
    
    def _utm_to_lat_long(self, utm_x, utm_y, zone, hemisphere):
        utm_proj = pyproj.Proj(proj='utm', zone=zone, datum='WGS84')
        wgs84_proj = pyproj.Proj(proj='latlong', datum='WGS84')
        
        long, lat = pyproj.transform(utm_proj, wgs84_proj, utm_x, utm_y)
        
        return lat, long
    
    def get_utm_coordinates(self):
        return self.utm_x, self.utm_y, self.psi
    
    def get_lat_long_coordinates(self):
        return self.lat, self.long, self.psi


def create_simulated_vehicle_nodes(
    namespace: str,
    start_position,
    goal_position,
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
    if isinstance(start_position, Position):
        x, y, psi = start_position.get_utm_coordinates()
    else:
        x, y, psi = start_position
    
    if isinstance(goal_position, Position):
        goal_x, goal_y, _ = goal_position.get_utm_coordinates()
    else:
        goal_x, goal_y = goal_position

    if composable:
        components = [
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
