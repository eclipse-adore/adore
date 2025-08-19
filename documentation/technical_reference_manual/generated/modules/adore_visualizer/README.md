# Visualization Node for Autonomous Systems

## Overview
The **Visualization Node** provides tools for visualizing autonomous vehicle states, trajectories, and maps. It integrates with ROS 2 and generates markers for visualization in RViz/Foxbox, enabling users to view and debug various aspects of autonomous driving systems.

---


## Included Modules

### Characters
**File:** `characters.hpp`
- Contains a map of ASCII characters to 5x7 pixel representations.
- Used for rendering text on visualizations.

### Color Palette
**File:** `color_palette.hpp`
- Defines a set of predefined colors based on the Tableau 10 palette.
- Includes utilities for HSV-to-RGB color conversion.

### Map Image Visualization
**File:** `map_image_visualization.hpp`
- Provides tools to convert map tiles into occupancy grids.
- Fetches map images and integrates them into visualization workflows.

### State Buffer
**File:** `state_buffer.hpp`
- Implements a time-based circular buffer for vehicle state data.
- Useful for creating time-history visualizations.

### Visualization Primitives
**File:** `visualization_primitives.hpp`
- Provides utilities for creating basic visualization markers:
  - Rectangles, spheres, and lines.
  - Finish lines and text markers.
- Supports flexible offsets and scaling.

### Visualizer
**File:** `visualizer.hpp`
- Implements the main node for visualization.
- Subscribes to various ROS 2 topics and publishes visualization markers for RViz.

### Visualizer Conversions
**File:** `visualizer_conversions.hpp`
- Converts ROS 2 messages (e.g., trajectories, maps, goals) into marker arrays.
- Includes support for traffic participant sets, safety corridors, and more.

---
