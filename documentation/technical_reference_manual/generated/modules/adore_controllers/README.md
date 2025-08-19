# ADORe Controller Library

## Overview

This library provides various controllers for trajectory tracking, designed for autonomous vehicle applications. The controllers can be used to compute control commands (acceleration, steering angle) based on the vehicle's state and a desired trajectory. The following controllers are included:

- **NMPC (Nonlinear Model Predictive Control)**
- **PID (Proportional-Integral-Derivative Control)**
- **iLQR (Iterative Linear Quadratic Regulator)**

These controllers are designed to be easily integrated into any vehicle trajectory tracking application and can be configured with custom vehicle limits and controller-specific parameters.

## Features

- **Modular Design**: Each controller can be used independently or in conjunction with others.
- **Configurable Limits**: Vehicle command limits (e.g., acceleration, steering angle) can be easily set.
- **Multiple Controllers**: Includes four types of controllers for different use cases and performance needs.

## Controllers

### NMPC (Nonlinear Model Predictive Control)
A sophisticated control method that optimizes a vehicle's trajectory over a prediction horizon. It accounts for constraints like limits on acceleration and steering.

### PID (Proportional-Integral-Derivative Control)
A simpler control method that adjusts the vehicle's steering and speed based on the difference between the desired trajectory and the actual vehicle state.

### iLQR (Iterative Linear Quadratic Regulator)
An advanced controller that computes an optimal control sequence based on a linear-quadratic approximation of the system's dynamics and cost function.
