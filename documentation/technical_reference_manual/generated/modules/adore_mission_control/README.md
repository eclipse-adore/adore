# Mission Control Node

## Overview
The **Mission Control Node** is responsible for managing vehicle missions, generating and updating routes, publishing goals, and visualizing lane center distances in real time. It integrates map data, dynamically updates routes based on vehicle state, and supports interactive goal-setting via ROS topics.

---

## Features
- **Route Management**:
  - Dynamically updates routes based on vehicle position and progress.
  - Handles off-route scenarios and regenerates routes to active goals.
- **Goal Management**:
  - Publishes goal points for other nodes in the system.
  - Supports interactive goal-setting via `/clicked_point/goal_position`.
- **Local Map Publishing**:
  - Publishes a cropped submap around the vehicle for local planning and visualization.

---

## Topics

### Published Topics
1. **`mission/goal_position`**
   - Type: `adore_ros2_msgs::msg::GoalPoint`
   - Description: Publishes the current goal position.

2. **`route`**
   - Type: `adore_ros2_msgs::msg::Route`
   - Description: Publishes the current route to the active goal.

3. **`local_map`**
   - Type: `adore_ros2_msgs::msg::Map`
   - Description: Publishes a cropped local map around the vehicle.

4. **`goal_reached`**
   - Type: `std_msgs::msg::Bool`
   - Description: Publishes `true` when the current goal is reached.


## Parameters

| Parameter Name      | Type   | Default Value | Description                        |
|---------------------|--------|---------------|------------------------------------|
| `goal_position_x`   | `double` | `0.0`       | X-coordinate of the initial goal. |
| `goal_position_y`   | `double` | `0.0`       | Y-coordinate of the initial goal. |
| `R2S map file`      | `string` | `""`        | Path to the R2S map file.         |

---


