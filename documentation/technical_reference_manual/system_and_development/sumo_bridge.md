# ADORe and SUMO
This document descries how to get ADORe and SUMO running together.


## sumo_bridge ROS2 node
The `sumo_bridge` is a ROS 2 node located in `ros2_workspace/src/adore_interfaces/sumo_bridge`
that bridges [SUMO](https://sumo.dlr.de) traffic simulation to the 
ADORe stack via libsumo. SUMO vehicles are published as `TrafficParticipantSet` 
messages and the ego vehicle state is injected back into SUMO each simulation step.

## Configuration

All variables are set in `adore.env`.

| Variable | Default | Description |
|---|---|---|
| `SUMO_BRIDGE_ENABLE` | `false` | Set to `true` to start the bridge |
| `SUMO_CONFIG_DIRECTORY` | `ros2_workspace/src/adore_interfaces/sumo_bridge/sumo_configs` | Path relative to `SOURCE_DIRECTORY` containing `.sumocfg` files |
| `SUMO_BRIDGE_CONFIG_FILE` | `demo_sumo_bridge.sumocfg` | Config filename. Sets `SUMO_CONFIG_FILE` in `adore.env` |
| `SUMO_HOME` | `/usr/share/sumo` | Path to SUMO installation |

## Starting

The bridge is managed as a host process via `start_sumo_bridge.sh`. It is started automatically when `SUMO_BRIDGE_ENABLE=true` is set in `adore.env`. The script is idempotent -- if the bridge is already running it exits cleanly.

```bash
bash tools/start_sumo_bridge.sh
```

Logs and PID are written to `${SOURCE_DIRECTORY}/.log/sumo_bridge/`.

## ROS Parameters

| Parameter | Type | Default | Description |
|---|---|---|---|
| `sumo_config_file` | `string` | `""` | Absolute path to the `.sumocfg` file. Required. |
| `sumo_step_length` | `double` | `0.01` | SUMO simulation step length in seconds |
| `use_gui` | `bool` | `false` | Launch `sumo-gui` instead of headless `sumo` |

## Topics

| Topic | Type | Direction | Description |
|---|---|---|---|
| `traffic_participants` | `TrafficParticipantSet` | publish | SUMO vehicles converted to ADORe traffic participants |
| `vehicle_state/traffic_participant` | `TrafficParticipant` | subscribe | Ego vehicle state injected into SUMO |

## Launch

Use `sumo_test.launch.py` for a full scenario including the ego vehicle stack and visualizer. The launch file reads `SUMO_CONFIG_FILE` and `SUMO_CONFIG_DIRECTORY` from the environment.

```bash
make cli
cd adore_scenarios/simulation_scenarios
ros2 launch sumo_bridge sumo_test.launch.py
```

To enable the SUMO GUI, set `use_gui:=True` on the `sumo_bridge` node in the launch file or pass it directly:

```bash
ros2 run sumo_bridge sumo_bridge --ros-args \
    --param "sumo_config_file:=<path>" \
    --param "use_gui:=true"
```
