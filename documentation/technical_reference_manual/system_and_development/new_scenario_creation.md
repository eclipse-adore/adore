# 🚗 How to Create a Scenario File
This guide walks you through the steps to create a custom scenario file for simulation or testing purposes.
---
## 📝 Steps
### 1. Copy an Existing Scenario
Start by copying any **working scenario file**. This ensures you have a valid structure and format to begin with.
```bash
cp template.launch.py my_custom_scenario.launch.py
```
---
### 2. Open the goal picking tool to select a goal:
1. Once the ADORe CLI is running with `make start` or `make cli` and navigate to the goal picker:
```bash
chromium "http://localhost:8888/?tab=goal-picker"
```
or use the direct link:
[http://localhost:8888/?tab=goal-picker](http://localhost:8888/?tab=goal-picker)

2. Use the goal picking tool to:
   - Search for locations using the search box
   - Click on the map to place start and goal markers
   - On the start point set the heading flag (this can be clicked and dragged). 
   - Toggle between start and goal placement modes
   - View coordinates in both Lat/Long and UTM formats
   - Copy the generated Python code directly from the text boxes
---
### 3. Get Start and Goal Coordinates
You can obtain coordinates using one of these methods:

**Method A: Goal Picker Tool (Recommended)**
- Use the **goal picker** tool as described above
- This tool provides both coordinate formats and generates Python code automatically
- Simply click on the map to place markers and copy the generated code

**Method B: Google Maps**
- Use [Google Maps](https://maps.google.com) to select your **desired start point** and **goal point**
- Right-click on the location and choose `What's here?`
- Copy the **latitude and longitude** for both start and goal points
---
### 4. Define Positions Using the New Position Class
You can now define positions using either **Lat/Long** or **UTM** coordinates with the new Position class:
```python
start_position = Position(lat_long=(52.315849, 10.562169), psi=0.0)
goal_positions = [
    Waypoint(Position(utm=(606471.04, 5797161.11, 32, "U")), WaypointBehavior.STOP),
]
```

> **💡TIP:** The Position class automatically converts between coordinate systems, so you can use whichever format is most convenient for your source data.
---
### 5. Update Your Scenario File
Open your scenario file and update the position definitions:

```python
from launch import LaunchDescription
from launch_ros.actions import Node
import sys
import os
sys.path.append(os.path.dirname(__file__))
from position import Position, Waypoint, WaypointBehavior
from simulated_vehicle import create_simulated_vehicle
from visualizer import create_visualizer

start_position = Position(lat_long=(52.315849, 10.562169), psi=0.0)
goal_positions = [
    Waypoint(Position(utm=(606471.04, 5797161.11, 32, "U")), WaypointBehavior.STOP),
]

def generate_launch_description():
    return LaunchDescription([
        *create_simulated_vehicle(
            namespace="ego_vehicle",
            start_position_utm=start_position.get_utm_coordinates(),
            goals=goal_positions,
            vehicle_id=111,
            v2x_id=0,
        ),
        *create_visualizer(
            whitelist=["ego_vehicle"],
            visualization_offset=start_position.get_utm_coordinates(),
        )
    ])

```
---
### 6. Set the Start Heading
The **start heading** (orientation in radians) can be critical for correct vehicle behavior:
- Try an initial value like `0.0` or `1.57` (90°).
- Adjust the heading using a **trial-and-error method** until the vehicle starts in the correct direction.
- The heading is specified as the `psi` parameter in the Position class or as the third element in the legacy tuple format.
- The heading can be calculated with the goal picker.
---

