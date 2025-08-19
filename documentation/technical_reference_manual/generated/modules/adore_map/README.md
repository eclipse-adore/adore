# Map Library for Autonomous Vehicles

## Overview
The **Map Library** provides  tools for handling map data in autonomous vehicle simulations. It includes modules for lane and route management, spatial querying using quadtree structures, geographic coordinate conversions. The library is designed for efficiency and integration with autonomous vehicle systems.

---

## Features
- **Lane and Route Management**:
  - Define and manage lanes, routes, and road networks.
- **Map Point and Spatial Data**:
  - Support for geospatial data handling and storage.
- **Quadtree Spatial Indexing**:
  - Efficient spatial querying.
- **Map Parsing and Loading**:
  - Tools for loading and parsing maps, including Road2Simulation (R2S) format support.
- **Geographic Conversions**:
  - Latitude/longitude to UTM coordinate transformations.


---

## Included Modules

### Lane Representation
**File:** `lane.hpp`
- Defines lane structures, attributes, and connectivity.
- Provides methods for querying lane information and relationships.

### Geographic Conversions
**File:** `lat_long_conversions.hpp`
- Implements conversions between latitude/longitude and UTM coordinates.

### Map Structure
**File:** `map.hpp`
- Core representation of the map, including roads, lanes and road graph.
- Supports high-level map querying and manipulation.

### Map Loader
**File:** `map_loader.hpp`
- Handles the loading of map data from external files or formats.
- Includes support for parsing the Road2Simulation (R2S) format.

### Map Point
**File:** `map_point.hpp`
- Represents individual points in the map.

### Quadtree Spatial Index
**File:** `quadtree.hpp`
- Provides efficient spatial indexing for querying.

### R2S Parser
**File:** `r2s_parser.h`
- Parses Road2Simulation (R2S) format maps into internal representations.

### Rasterizer
**File:** `rasterizer.hpp`
- Converts map representations into raster images for visualization or analysis.
- Supports configurable resolution and layers.

### Road Graph
**File:** `road_graph.hpp`
- Represents the map as a graph of lanes.
- Supports pathfinding.

### Route Handling
**File:** `route.hpp`
- Defines and manages routes within the map.
- Includes tools for route planning.

---

