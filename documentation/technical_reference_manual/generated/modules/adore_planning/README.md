# Planning Library for Autonomous Vehicles

## Overview
The **Planning Library** provides advanced tools for trajectory planning and optimization in autonomous vehicles. It includes components for lane following, safety corridor planning, trust region optimization, and utilities to convert high-level routes into executable trajectories. Designed for efficiency, the library integrates optimization techniques and vehicle dynamics models.

---

## Features
- **Lane Following**:
  - Implements trajectory planning to maintain a target route.
- **Safety Corridor Planning**:
  - Plans trajectories within predefined safety corridors.
- **Trajectory Optimization**:
  - Leverages Model Predictive Control (MPC) with Nonlinear Programming for optimal trajectory generation.
- **Trust Region Optimization**:
  - Solves cooperative multi-agent planning problems using trust region solvers.
- **Planning Helpers**:
  - Utilities for waypoint filtering, point shifting, and trajectory conversion.

---

## Included Modules

### Lane Follow Planner
**File:** `lane_follow_planner.hpp`
- Implements lane-following behavior by generating trajectories that align with the centerline of a given route.
- Considers vehicle dynamics, curvature, and control limits.

### OptiNLC Trajectory Optimizer
**File:** `optinlc_trajectory_optimizer.hpp`
- Performs trajectory optimization using Model Predictive Control (MPC).
- Optimizes trajectories by solving nonlinear constrained optimization problems.
- Features customizable weights for objectives like lateral error, heading error, and steering input.

### OptiNLC Trajectory Planner
**File:** `optinlc_trajectory_planner.hpp`
- Converts high-level routes into optimized trajectories using MPC.
- Supports curvature-based velocity profiling and piecewise polynomial representations of routes.

### Planning Helpers
**File:** `planning_helpers.hpp`
- Provides utility functions for planning, such as:
  - Filtering waypoints in front of the vehicle.
  - Shifting points laterally for safety or desired offsets.
  - Converting waypoints into executable trajectories.

### Safety Corridor Planner
**File:** `safety_corridor_planner.hpp`
- Plans trajectories within a defined safety corridor.
- Uses polynomial representations for corridor boundaries.
- Implements constraints to ensure the vehicle remains within safe zones.

### Trust Region Solver
**File:** `trust_region_solver.hpp`
- Solves multi-agent planning problems using trust region optimization.
- Models each agent's trajectory and controls, ensuring convergence through gradient-based optimization.

---

