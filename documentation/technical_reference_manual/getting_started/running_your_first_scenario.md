# Running Your First Scenario

> **ℹ️INFO:**
> Visualization requires a chrome based browser (see: https://www.chromium.org/chromium-projects/) 

1. Start `lichtblick suite` aka `foxglove` aka `foxbox`.
see the [ADORe Lichtblick-Suite README 🔗](../generated/visualization/lichtblick/README.md). 

2. Run a scenario, launch or attach to the `ADORe CLI` from the root of the `ADORe` repo:
```bash
just dev
cd adore_scenarios/simulation_scenarios
ros2 launch simulation_test.launch.py
```

3. In a separate tab, start Lichtblick visualization
```bash
just lichtblick
```
Then open the displayed URL with chome based browser. 

Some visualization layouts are available in tools/lichtblick/lichtblick_layouts


## Running A Scenario With The ADORe Mission Control Web Interface
1. Start `lichtblick suite` aka `foxglove` aka `foxbox`.
see the [ADORe Lichtblick-Suite README 🔗](../generated/visualization/lichtblick/README.md). 

2. start the `ADORe CLI` from the root of the `ADORe` repo:
```bash
just dev
```

or

```bash
./.docker/scripts/run_dev.sh
```

3. Start the adore API
```bash
just api_start
```


4. Open the web based gui
[http://localhost:8888](http://localhost:8888)

5. Select a scenario in the `Senario Manager` and click start

6. Switch to the `Visualization` tab to visualize the scenario

See the [ADORe Mission Control README 🔗](../generated/api/adore_api/adore_mission_control.md) for more information on the `ADORe Mission Control`. 
