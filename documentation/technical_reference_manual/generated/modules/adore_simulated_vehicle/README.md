# Simulated Vehicle Node

## Overview
The **Simulated Vehicle Node** is part of the Eclipse ADORe project. It simulates a vehicle's dynamics and publishes its state while integrating with other simulated traffic participants. This node provides control interfaces, state publishers, and supports noise injection for simulation fidelity.

## Features
- **Vehicle Dynamics Simulation**: Simulates a vehicle using a physical model (e.g., bicycle model).
- **Noise Injection**: Adds configurable noise to position, velocity, yaw, and acceleration for realistic simulation.
- **State Publishing**:
  - Vehicle dynamic state
  - Odometry for localization
  - Traffic participant data
- **Multi-Vehicle Simulation**: Subscribes to the states of other vehicles in the simulation to provide context-aware traffic interactions.
- **Control Interfaces**:
  - Supports both manual control via teleoperation.
  - Automated vehicle control.

---

## Topics

### Published Topics
1. **`vehicle_state/dynamic`**
   - Message Type: `adore_ros2_msgs::msg::VehicleStateDynamic`
   - Description: Publishes the current dynamic state of the simulated vehicle.

2. **`vehicle_state/localization`**
   - Message Type: `nav_msgs::msg::Odometry`
   - Description: Provides odometry data for localization purposes.

3. **`vehicle_state/monitor`**
   - Message Type: `adore_ros2_msgs::msg::StateMonitor`
   - Description: Publishes localization error metrics.

4. **`traffic_participants`**
   - Message Type: `adore_ros2_msgs::msg::TrafficParticipantSet`
   - Description: Publishes the state of surrounding simulated traffic participants.

### Subscribed Topics
1. **`next_vehicle_command`**
   - Message Type: `adore_ros2_msgs::msg::VehicleCommand`
   - Description: Receives commands for steering and acceleration.

2. **`teleop_controller`**
   - Message Type: `geometry_msgs::msg::Twist`
   - Description: Accepts manual control inputs for teleoperation.

3. **`automation_toggle`**
   - Message Type: `std_msgs::msg::Bool`
   - Description: Toggles between manual and automated control.

4. **`/<namespace>/vehicle_state/localization`**
   - Message Type: `nav_msgs::msg::Odometry`
   - Description: Subscribes to localization data from other vehicles.

---

## Parameters

| Parameter Name               | Type                | Default Value | Description                                |
|------------------------------|---------------------|---------------|--------------------------------------------|
| `controllable`               | `bool`             | `true`        | Determines if the vehicle is controllable. |
| `set_start_position_x`       | `double`           | `0.0`         | Initial x-coordinate of the vehicle.       |
| `set_start_position_y`       | `0.0`              | `double`      | Initial y-coordinate of the vehicle.       |
| `set_start_psi`              | `0.0`              | `double`      | Initial yaw angle of the vehicle.          |
| `position_noise_stddev`      | `double`           | `0.0`         | Standard deviation for position noise.     |
| `velocity_noise_stddev`      | `double`           | `0.0`         | Standard deviation for velocity noise.     |
| `yaw_noise_stddev`           | `double`           | `0.0`         | Standard deviation for yaw noise.          |
| `acceleration_noise_stddev`  | `double`           | `0.0`         | Standard deviation for acceleration noise. |
| `other_vehicle_namespaces`   | `list<string>`     | `[]`          | List of other vehicle namespaces.          |

---

## How It Works
1. **Initialization**:
   - Loads configuration parameters.
   - Sets up publishers, subscribers, and noise distributions.
2. **Simulation**:
   - Simulates vehicle dynamics using a physical model.
   - Injects configurable noise into the vehicle state.
3. **Publishing and Subscribing**:
   - Publishes its dynamic state and subscribes to other vehicles' states.
   - Broadcasts the simulated vehicle's transform for integration with ROS 2 TF.
4. **Traffic Participant Updates**:
   - Computes distances to other vehicles and publishes a list of relevant traffic participants.

---


