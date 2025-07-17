# 🚗 How to Create a Scenario File
This guide walks you through the steps to create a custom scenario file for simulation or testing purposes.
---
## 📝 Steps
### 1. Copy an Existing Scenario
Start by copying any **working scenario file**. This ensures you have a valid structure and format to begin with.
```bash
cp existing_scenario.py my_custom_scenario.py
```
---
### 2. Start the Goal Picking Tool
To use the interactive goal picker tool:

1. Start `lichtblick suite` from the `ADORe` project root:
```bash
cd tools/lichtblick
make build
make start
```

2. Open the goal picker tool in your browser:
```bash
chromium http://localhost:8080/assets/goal_picker.html
```
or use the direct link:
[http://localhost:8080/assets/goal_picker.html](http://localhost:8080/assets/goal_picker.html)

3. Use the tool to:
   - Search for locations using the search box
   - Click on the map to place start and goal markers
   - Toggle between start and goal placement modes
   - View coordinates in both Lat/Long and UTM formats
   - Copy the generated Python code directly from the text boxes
---
### 3. Get Start and Goal Coordinates
You can obtain coordinates using one of these methods:

**Method A: Goal Picker Tool (Recommended)**
- Use the **goal_picker.html** tool as described above
- This tool provides both coordinate formats and generates Python code automatically
- Simply click on the map to place markers and copy the generated code

**Method B: Google Maps**
- Use [Google Maps](https://maps.google.com) to select your **desired start point** and **goal point**
- Right-click on the location and choose `What's here?`
- Copy the **latitude and longitude** for both start and goal points
---
### 4. Define Positions Using the New Position Class
You can now define positions using either **Lat/Long** or **UTM** coordinates with the new Position class:

**Option A: Using Lat/Long coordinates**
```python
from scenario_helpers.simulated_vehicle import Position

start_position = Position(lat_long=(52.314562, 10.560474), psi=0.0)
goal_position = Position(lat_long=(52.313533, 10.560554))
```

**Option B: Using UTM coordinates**
```python
from scenario_helpers.simulated_vehicle import Position

start_position = Position(utm=(606372, 5797172, 32, 'N'), psi=0.0)
goal_position = Position(utm=(606380, 5797058, 32, 'N'))
```

**Option C: Legacy tuple format (still supported)**
```python
start_position = (606529.67, 5797315.01, -3.23)
goal_position = (606447.98, 5797272.22)
```

> **💡TIP:** The Position class automatically converts between coordinate systems, so you can use whichever format is most convenient for your source data.
---
### 5. Update Your Scenario File
Open your scenario file and update the position definitions:

```python
from scenario_helpers.simulated_vehicle import Position

start_position = Position(lat_long=(52.314562, 10.560474), psi=3.04)
goal_position = Position(lat_long=(52.313533, 10.560554))

def generate_launch_description():
    return LaunchDescription([
        *create_simulated_vehicle_nodes(
            namespace="ego_vehicle",
            start_position=start_position,
            goal_position=goal_position,
            map_file=map_file,
            model_file=vehicle_model_file,
            # ... other parameters
        )
    ])
```
---
### 6. Set the Start Heading
The **start heading** (orientation in radians) can be critical for correct vehicle behavior:
- Try an initial value like `0.0` or `1.57` (90°).
- Adjust the heading using a **trial-and-error method** until the vehicle starts in the correct direction.
- The heading is specified as the `psi` parameter in the Position class or as the third element in the legacy tuple format.
---
## ✅ Example Entry

**New Position class format:**
```python
from scenario_helpers.simulated_vehicle import Position

start_position = Position(lat_long=(52.314562, 10.560474), psi=3.04)
goal_position = Position(lat_long=(52.313533, 10.560554))
```

**Alternative UTM format:**
```python
from scenario_helpers.simulated_vehicle import Position

start_position = Position(utm=(606372, 5797172, 32, 'N'), psi=3.04)
goal_position = Position(utm=(606380, 5797058, 32, 'N'))
```

**Legacy tuple format:**
```python
start_position = (606529.67, 5797315.01, -3.23)
goal_position = (606447.98, 5797272.22)
```
---
## 🔁 Final Check
Before running the scenario:
- ✅ Validate the file syntax.
- ✅ Make sure start and goal positions make sense visually.
- ✅ Run the simulation and fine-tune as needed.
- ✅ Test both coordinate formats to ensure compatibility.
- ✅ Verify the import statement for the Position class is included.
---
