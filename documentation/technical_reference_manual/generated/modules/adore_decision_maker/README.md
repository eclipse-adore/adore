# Decision Maker Node

## Overview
The **Decision Maker Node** orchestrates the vehicle's behavior by determining the appropriate operational state based on real-time conditions and data inputs. It ensures safe, efficient, and responsive driving through a state-based decision-making framework, integrating route planning, trajectory generation, and safety corridor management.

---

## Features
- **State-Based Decision Making**:
  - Seven operational states, prioritized by criticality:
    1. **Safety Corridor**: Navigate within a safety corridor.
    2. **Remote Operation**: Operate under remote control.
    3. **Requesting Assistance**: Handle assistance requests.
    4. **Follow Route**: Follow a predefined route.
    5. **Follow Reference**: Track a given trajectory.
    6. **Standstill**: Halt the vehicle.
    7. **Emergency Stop**: Stop immediately in critical situations.
- **Route Planning and Trajectory Generation**:
  - Supports multiple planners: Lane Following and OptiNLC.
  - Dynamically generates trajectories based on current conditions.
- **Safety Corridor Handling**:
  - Manages trajectories to navigate or escape safety corridors.
  - Supports both JSON and DENM-based safety corridor formats.
- **Remote Operation Support**:
  - Follows waypoints provided during remote operations.
- **Dynamic Environment Awareness**:
  - Adapts to real-time updates from maps, routes, and vehicle states.

---

## Topics

### Published Topics
1. **`trajectory_decision`**
   - Type: `adore_ros2_msgs::msg::Trajectory`
   - Description: Publishes the generated trajectory for execution.

2. **`/MAV/control/RO/path_suggestion`**
   - Type: `std_msgs::msg::String`
   - Description: Suggests an alternative trajectory during remote operations.

3. **`remote_operations_driving_status`**
   - Type: `adore_ros2_msgs::msg::RemoteOperationsDrivingStatus`
   - Description: Publishes the status of remote driving operations.

4. **`/MAV/state/modes`**
   - Type: `std_msgs::msg::String`
   - Description: Notifies the system of the current driving mode.

5. **`/MAV/state/position`**
   - Type: `std_msgs::msg::String`
   - Description: Publishes the vehicle's position during remote operations.

### Subscribed Topics
1. **`route`**
   - Type: `adore_ros2_msgs::msg::Route`
   - Description: Receives the current planned route.

2. **`vehicle_state/dynamic`**
   - Type: `adore_ros2_msgs::msg::VehicleStateDynamic`
   - Description: Updates the vehicle's dynamic state.

3. **`local_map`**
   - Type: `adore_ros2_msgs::msg::Map`
   - Description: Receives updates on the local map.

4. **`/ego_vehicle/v2x/json/rgs`**
   - Type: `std_msgs::msg::String`
   - Description: Receives safety corridor data in JSON format.

5. **`/DENM_out`**
   - Type: `denm_v2_23_denm_pdu_description_msgs::msg::DENM`
   - Description: Receives safety corridor data in DENM format.

6. **`vehicle_state/monitor`**
   - Type: `adore_ros2_msgs::msg::StateMonitor`
   - Description: Monitors the vehicle's localization and state.

7. **`/MAV/control/waypoint_suggestion`**
   - Type: `std_msgs::msg::String`
   - Description: Receives waypoint suggestions for remote operation.

8. **`planned_trajectory`**
   - Type: `adore_ros2_msgs::msg::Trajectory`
   - Description: Receives a pre-planned trajectory to follow.

9. **`traffic_signals`**
   - Type: `adore_ros2_msgs::msg::TrafficSignals`
   - Description: Updates traffic signal information.

---

## Parameters

| Parameter Name                 | Type      | Default Value | Description                                                   |
|--------------------------------|-----------|---------------|---------------------------------------------------------------|
| `debug_mode_active`            | `bool`    | `true`        | Enables or disables debug logging.                           |
| `use_reference_trajectory_as_is` | `bool`  | `true`        | Uses the reference trajectory directly without optimization. |
| `set_route_planner`            | `int`     | `0`           | Sets the route planner (0: Lane Following, 1: OptiNLC).      |
| `dt`                           | `double`  | `0.05`        | Control loop time step (seconds).                            |
| `remote_operation_speed`       | `double`  | `2.0`         | Speed during remote operation (m/s).                         |
| `max_acceleration`             | `double`  | `2.0`         | Maximum allowed acceleration (m/s²).                         |
| `min_acceleration`             | `double`  | `-2.0`        | Minimum allowed acceleration (m/s²).                         |
| `max_steering`                 | `double`  | `0.7`         | Maximum allowed steering angle (radians).                    |

---

## States

### State Prioritization
States are evaluated in the following priority order:
1. **Safety Corridor**:
   - Conditions: `VEHICLE_STATE_OK` and `SAFETY_CORRIDOR_PRESENT`.
   - Generates a trajectory within or escaping the safety corridor.
2. **Remote Operation**:
   - Conditions: `VEHICLE_STATE_OK` and `WAYPOINTS_AVAILABLE`.
   - Follows waypoints during remote control.
3. **Requesting Assistance**:
   - Conditions: `VEHICLE_STATE_OK` and `NEED_ASSISTANCE`.
   - Generates a standstill trajectory and requests assistance.
4. **Follow Route**:
   - Conditions: `VEHICLE_STATE_OK`, `ROUTE_AVAILABLE`, and `LOCAL_MAP_AVAILABLE`.
   - Generates a trajectory to follow a planned route.
5. **Follow Reference**:
   - Conditions: `VEHICLE_STATE_OK` and `REFERENCE_TRAJECTORY_VALID`.
   - Tracks the provided trajectory.
6. **Standstill**:
   - Conditions: `VEHICLE_STATE_OK`.
   - Generates a standstill trajectory.
7. **Emergency Stop**:
   - Conditions: None.
   - Stops the vehicle immediately.

---
