# Trajectory Tracker Node

## Overview

The **Trajectory Tracker Node** is a ROS 2 node designed to track and execute vehicle trajectories. It supports multiple controllers that calculate the optimal control commands (acceleration and steering) based on the current vehicle state and a desired trajectory.

### Features

- **Multiple Controllers Supported**: The node supports different controllers for trajectory tracking, including:
  - **NMPC** (Nonlinear Model Predictive Controller)
  - **PID** (Proportional-Integral-Derivative Controller)
  - **iLQR** (Iterative Linear Quadratic Regulator)
- **Real-time Control**: The node operates in real-time, constantly computing and publishing vehicle commands.
- **Configurable via ROS 2 Parameters**: You can dynamically choose which controller to use and configure controller parameters via ROS 2 launch files or parameter servers.

## Controllers

- **NMPC**: Optimizes the trajectory over a prediction horizon while respecting control and vehicle limits.
- **PID**: Adjusts steering and speed based on the error between the current state and the desired trajectory.
- **iLQR**: Computes the optimal control commands using iterative linear quadratic methods.

## ROS 2 Parameters

- **`set_controller`** (int): Defines which controller to use. Options:
  - `0`: NMPC (default)
  - `1`: PID
  - `3`: iLQR
- **`controller_settings`**: A dictionary of controller-specific parameters. Each controller can be configured with different settings (e.g., PID gains, NMPC weights). These are given in two vectors: keys (string) and values (double)
- **`vehicle_type`** (string): Specifies the type of vehicle being controlled, e.g., "simulation" or a real-world vehicle type.

## Topics

- **Published Topics**:
  - `/next_vehicle_command` (`adore_ros2_msgs::msg::VehicleCommand`): The next control command (acceleration, steering) for the vehicle.

- **Subscribed Topics**:
  - `/planned_trajectory` (`adore_ros2_msgs::msg::Trajectory`): The desired trajectory the vehicle should follow.
  - `/vehicle_state/dynamic` (`adore_ros2_msgs::msg::VehicleStateDynamic`): The current dynamic state of the vehicle (e.g., position, velocity, yaw).
  - `/choosen_decision_maker` (`adore_ros2_msgs::msg::DecisionMakerSelect`): The decision-maker selecting the mode (normal or emergency).
