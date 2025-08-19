# Vehicle Dynamics Library

## Overview
This library provides tools for simulating vehicle dynamics, integrating physical models, and managing vehicle states and commands. The components are modular and designed to support the simulation of autonomous vehicles, including trajectory planning and control-

---

## Features
- **Integration Methods**:
  - Efficient Runge-Kutta 4th order (RK4) integration for dynamic systems.
- **Physical Vehicle Models**:
  - Predefined parameters for common vehicle models (e.g., bicycle model).
- **Trajectory Handling**:
  - Support for trajectory generation and interpolation.
- **Vehicle State Management**:
  - Classes for managing vehicle states and transitions.
- **Vehicle Command Abstractions**:
  - Structures to encapsulate commands such as steering, acceleration.

---

## Included Modules

### Integration
**File:** `integration.hpp`
- Provides tools for numerical integration
- Core functionality for advancing dynamic systems in time.


### Physical Vehicle Parameters
**File:** `physical_vehicle_parameters.hpp`
- Contains parameter definitions for vehicle models.
- Includes attributes such as wheelbase, mass, and maximum steering angles.

### Trajectory Handling
**File:** `trajectory.hpp`
- Provides trajectory representations and interpolation methods.

### Vehicle Command
**File:** `vehicle_command.hpp`
- Encapsulates vehicle control commands - steering angles and acceleration.

### Vehicle State
**File:** `vehicle_state.hpp`
- Manages the state of a simulated vehicle, including position, velocity, and orientation.
- Provides methods for state updates and transformations.

---

