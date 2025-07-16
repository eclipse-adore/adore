# Running a Scenario
This guide will walk through running and visualizing a scenario.

### Scenario Executions
1. Launch or attach to the `ADORe CLI` from the root of the `ADORe` repo:
```bash
make cli
```

2. `cd` to scenario directory:
```bash
cd adore_scenarios/simulation_scenarios
```

3. Launch a scenario:
```bash
ros2 launch simulation_test.py
```

### Scenario Visualization

> **ℹ️INFO:**
> Visualization requires a chrome based browser (see: https://www.chromium.org/chromium-projects/) 

1. Start `lichtblick suite` aka `foxglove` aka `foxbox`. From the `ADORe` project root run:
```bash
cd tools/lichtblick
make build
make start
```

2. Run a scenario, launch or attach to the `ADORe CLI` from the root of the `ADORe` repo:
```bash
make cli
cd adore_scenarios/simulation_scenarios
ros2 launch simulation_test.py
```

3. Open lichtblick (in another shell):
```bash
chromium http://localhost:8080/\?ds\=foxglove-websocket\&ds.url\=ws://localhost:8765\&layout\=Default.json
```
or with a link:
[http://localhost:8080/?ds=foxglove-websocket&ds.url=ws://localhost:8765&layout=Default.json](http://localhost:8080/?ds=foxglove-websocket&ds.url=ws://localhost:8765&layout=Default.json)


## Creating a Scenario: How to Create a Scenario File

This guide walks you through the steps to create a custom scenario file for simulation or testing purposes.

---

### 1. Copy an Existing Scenario
Start by copying any **working scenario file**. This ensures you have a valid structure and format to begin with.

```bash
cp existing_scenario.py my_custom_scenario.py
```

---

### 2. Get Start and Goal Coordinates
Use [Google Maps](https://maps.google.com) to select your **desired start point** and **goal point**.

- Right-click on the location and choose `What's here?`
- Copy the **latitude and longitude** for both start and goal points.

---

### 3. Convert Lat/Lon to UTM
Convert the geographic coordinates to **UTM (Universal Transverse Mercator)** format.

You can use this free online tool:

👉 [https://www.latlong.net/lat-long-utm.html](https://www.latlong.net/lat-long-utm.html)

Paste the latitude and longitude into the tool, and copy the resulting **UTM coordinates**.

---

### 4. Replace Start and Goal in the Scenario
Open the scenario or launch file and:

- Replace the original **start_pose** with the converted UTM coordinates.
- Replace the original **goal_position** with the converted UTM coordinates.

---

### 5. Set the Start Heading
The **start heading** (orientation in radians or degrees) can be critical to correct vehicle behavior.

- Try an initial value like `0.0` or `1.57` (90°).
- Adjust the heading using a **trial-and-error method** until the vehicle starts in the correct direction.

---

✅ Example Entry:
```
start_pose=(606529.67, 5797315.01, -3.23),
goal_position=(606447.98, 5797272.22)
```

---

## 🔁 Final Check
Before running the scenario:

- ✅ Validate the file syntax.
- ✅ Make sure start and goal positions make sense visually.
- ✅ Run the simulation and fine-tune as needed.

---
