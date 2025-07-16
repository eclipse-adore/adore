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

## ✅ Example Entry

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