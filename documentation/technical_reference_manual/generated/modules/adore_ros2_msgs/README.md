# ADORe ROS2 Messages

## Overview
Repository for common ADORe messages

## Message overview
MapConnection.msg
MapPoint.msg
MapLane.msg
MapRoad.msg
GoalPoint.msg
Map.msg
Route.msg
TrafficSignal.msg
TrafficSignals.msg
VehicleStateDynamic.msg
SafetyCorridor.msg
IndicatorState.msg
Trajectory.msg
VehicleCommand.msg
GearState.msg
VehicleInfo.msg

| Message | Description | Key Fields | Aliases/Search Terms |
|---------|-------------|------------|---------------------|
| **VehicleStateDynamic** | Core vehicle motion state | x, y, z, vx, vy, yaw_angle, yaw_rate, steering_angle, ax, ay, time | velocity, speed, position, acceleration, pose, heading, dynamics |
| **VehicleStateExtended** | Complete vehicle state with commands and info | state, last_command, info, header | full_state, extended_state, complete_vehicle_data |
| **VehicleCommand** | Control commands for vehicle actuation | steering_angle, acceleration | control, actuation, commands, steering, throttle, brake |
| **VehicleInfo** | Vehicle capabilities and status | id, gear_state, indicators, automatic_steering_on, physical_parameters | vehicle_status, capabilities, automation_level, gear |
| **Trajectory** | Planned vehicle trajectory | states[], request_id, label, header | path, plan, trajectory_planning, motion_plan |
| **TrafficParticipant** | Detected traffic entity with full state | motion_state, predicted_trajectory, classification, tracking_id | other_vehicles, obstacles, detection, tracking |
| **TrafficParticipantSet** | Collection of detected traffic participants | data[], validity_area, header | traffic_detection, object_list, perception_data |
| **Route** | Navigation route from start to goal | sections[], center_points[], start, goal | navigation, path_planning, routing, waypoint_following |
| **Map** | Road network structure | connections[], roads[], x_min, y_min, x_max, y_max | road_map, topology, lane_map, navigation_map |
| **PhysicalVehicleParameters** | Vehicle physical characteristics | wheelbase, mass, cog_to_front_axle, steering_ratio, body_width | vehicle_model, dynamics_parameters, physical_properties |
| **SafetyCorridor** | Drivable safety boundaries | left_border[], right_border[], header | safety_bounds, drivable_area, collision_avoidance |
| **TrafficSignal** | Traffic light state and position | x, y, signal_group_id, state (RED/YELLOW/GREEN) | traffic_lights, intersection_control, signal_phase |
| **Waypoints** | Navigation waypoints with speed limits | waypoints[], speed_limits[], label | waypoint_navigation, reference_path, speed_profile |
| **MapLane** | Lane geometry and properties | inner_points[], outer_points[], center_points[], speed_limit | lane_geometry, lane_boundaries, speed_limits |
| **TrafficClassification** | Object type classification | type_id (CAR, TRUCK, PEDESTRIAN, etc.) | object_classification, vehicle_type, detection_class |
| **TrafficParticipantDetection** | Detection with sensor information | participant_data, detection_by_sensor (RADAR, LIDAR, etc.) | sensor_fusion, detection_source, multi_modal |
| **GearState** | Transmission state | gear_state (NEUTRAL, DRIVING, REVERSE, PARKING) | transmission, gear_selection, drive_mode |
| **AssistanceRequest** | Driver assistance needed flag | state, assistance_needed | driver_assistance, takeover_request, intervention |
| **VehiclePrediction** | Predicted vehicle trajectory | id, trajectory_prediction | trajectory_prediction, motion_prediction, future_path |
| **TrafficPrediction** | Multi-vehicle trajectory predictions | traffic_prediction[] | traffic_prediction, multi_agent_prediction |
| **GoalPoint** | Navigation destination | x_position, y_position, id, time | destination, target, navigation_goal |
| **CautionZone** | Warning area polygon | label, polygon | warning_zone, hazard_area, caution_region |
| **MapRoad** | Road segment with lanes | road_id, name, one_way, lanes[], category | road_segment, highway, street, road_type |
| **RouteSection** | Section of planned route | lane_id, route_s, start_s, end_s | route_segment, path_section, lane_following |
| **TrafficSignals** | Multiple traffic signal states | signals[], header | intersection_signals, traffic_light_array |
| **StateMonitor** | System health monitoring | localization_error, localization_frequency, detection_frequency | system_health, monitoring, diagnostics |
| **IndicatorState** | Turn signal status | left_indicator_on, right_indicator_on | turn_signals, blinkers, indicators |
| **MapConnection** | Road network connectivity | from_id, to_id, connection_type, weight | road_topology, graph_edges, connectivity |
| **MapPoint** | Geographic point with metadata | x, y, s, max_speed, parent_id | map_coordinates, reference_point, lane_point |
| **TrajectoryTranspose** | Column-oriented trajectory data | x[], y[], vx[], vy[], yaw_angle[], time[] | trajectory_arrays, motion_data, time_series |
| **InfrastructureInfo** | Infrastructure element data | position_x, position_y, yaw, validity_area | infrastructure, roadside_units, v2i |
| **VisualizableObject** | Object for visualization | x, y, z, yaw, model | visualization, rendering, display_object |
| **Polygon2d** | 2D polygon geometry | points[] | geometry, polygon, boundary, area |
| **Point2d** | 2D coordinate point | x, y | coordinates, position, point, location |


