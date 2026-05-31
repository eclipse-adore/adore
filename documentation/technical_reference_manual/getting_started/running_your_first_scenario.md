# Running Your First Scenario

> **ℹ️INFO:**
> Visualization requires a chrome based browser (see: https://www.chromium.org/chromium-projects/) 

1. Start `lichtblick suite` aka `foxglove` aka `foxbox`.
see the [ADORe Lichtblick-Suite README 🔗](../generated/visualization/lichtblick/README.md). 

2. Run a scenario, launch or attach to the `ADORe CLI` from the root of the `ADORe` repo:
```bash
make cli
cd adore_scenarios/simulation_scenarios
ros2 launch simulation_test.launch.py
```

3. Open lichtblick (in another shell):
```bash
chromium  http://localhost:8080//?ds=rosbridge-websocket&ds.url=ws://localhost:9090&ds\=rosbridge-websocket\&layout\=Default.json
```
or with a link:
[http://localhost:8080//?ds=rosbridge-websocket&ds.url=ws://localhost:9090&ds\=rosbridge-websocket\&layout\=Default.json](http://localhost:8080//?ds=rosbridge-websocket&ds.url=ws://localhost:9090&ds\=rosbridge-websocket\&layout\=Default.json)

## Running A Scenario With The ADORe Mission Control Web Interface
1. Start `lichtblick suite` aka `foxglove` aka `foxbox`.
see the [ADORe Lichtblick-Suite README 🔗](../generated/visualization/lichtblick/README.md). 

2. start the `ADORe CLI` from the root of the `ADORe` repo:
```bash
make cli
```
or headlessly:
```bash
make start
```

The ADORe Mission Control will automatically start with the ADORe CLI.

3. Open the ADORe Mission Control
[http://localhost:8888](http://localhost:8888)

4. Select a scenario in the `Senario Manager` and click start

5. Switch to the `Visualization` tab to visualize the scenario

See the [ADORe Mission Control README 🔗](../generated/api/adore_api/adore_mission_control.md) for more information on the `ADORe Mission Control`. 
