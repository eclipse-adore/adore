# hardware_monitor

ROS 2 package that publishes hardware inventory and runtime status for every node in a cluster. Designed to be consumed by the ADORe Mission Control dashboard or any subscriber.

## Nodes

| Node | Topic | Rate | Content |
|------|-------|------|---------|
| `hardware_discovery_node` | `/cluster/<hostname>/hardware_inventory` | 0.1 Hz | Static inventory: CPU, RAM, GPU/NPU, PCI, USB, serial, storage, sensors, network interfaces with addresses |
| `hardware_status_node` | `/cluster/<hostname>/hardware_status` | 0.1 Hz | Runtime metrics: CPU load per-core, RAM/swap, GPU utilization, disk usage, temperatures, network I/O, NTP sync, process count |

Both topics publish `std_msgs/String` containing a JSON object. The hostname segment in the topic name is sanitized (hyphens replaced with underscores); the original hostname is preserved inside the JSON payload under `"hostname"`.

## Build

```bash
cd ros2_workspace
colcon build --packages-select hardware_monitor
source install/setup.bash
pip3 install -r src/adore_interfaces/hardware_monitor/requirements.pip3
```

## Run

```bash
# Start both nodes via launch file
./start.sh

# Stop
./stop.sh
```

Logs go to `${ROS_LOG_DIR}` → `${ROS_HOME}/log` → `~/.ros/log`.

## Configuration

`config/hardware_monitor.yaml` controls publish rates and warning thresholds:

```yaml
hardware_discovery_node:
  ros__parameters:
    publish_rate_hz: 0.1      # every 10 s is appropriate for static hardware

hardware_status_node:
  ros__parameters:
    publish_rate_hz: 0.1
    cpu_warn_percent: 85.0
    ram_warn_percent: 85.0
    disk_warn_percent: 85.0
    temp_warn_celsius: 80.0
```

Set `node_name` in either section to override the hostname used as the topic segment and JSON identifier.

## ADORe Mission Control integration

`hardware_monitor_api.py` is a Flask blueprint that:
- Starts and supervises both nodes **in-process** (no `ros2 run`, no PATH dependency)
- Subscribes to all `/cluster/+/hardware_*` topics and caches data per host
- Restarts crashed nodes automatically every 5 seconds


```python
from hardware_monitor.hardware_monitor_api import get_hardware_monitor_blueprint
app.register_blueprint(get_hardware_monitor_blueprint())
```

### API endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/hardware/hosts` | All known hosts and data availability |
| `GET` | `/api/hardware/hosts/<host>/status` | Latest status for one host |
| `GET` | `/api/hardware/hosts/<host>/inventory` | Latest inventory for one host |
| `GET` | `/api/hardware/hosts/<host>/stream` | SSE live status stream for one host |
| `GET` | `/api/hardware/stream` | SSE stream for all hosts `{host, data}` |
| `GET` | `/api/hardware/nodes/status` | Supervisor process health |
| `GET` | `/api/hardware/cache/status` | Cache freshness per host |

### Standalone web UI

```bash
./start_web_ui.sh          # default port 8889
HARDWARE_MONITOR_UI_PORT=9000 ./start_web_ui.sh
./stop_web_ui.sh
```

The UI is also embedded in ADORe Mission Control as the **Hardware Monitor** tab. It shows a cluster overview grid (one card per host) and per-host detail views for CPU, memory, network, storage, GPU/NPU, temperatures, and the full hardware inventory.

## Package structure

```
hardware_monitor/
├── hardware_monitor/
│   ├── hardware_discovery_node.py   # inventory publisher
│   ├── hardware_status_node.py      # runtime metrics publisher
│   ├── hardware_utils.py            # hardware probing (sysfs, psutil, lsblk, lsusb)
│   └── hardware_monitor_api.py      # Flask blueprint + node supervisor
├── web_ui/
│   ├── hardware_monitor_web.py      # standalone Flask app
│   ├── static/hardware_monitor_panel.js   # self-contained dashboard component
│   └── templates/hardware_monitor.html    # standalone page template
├── config/hardware_monitor.yaml
├── launch/hardware_monitor.launch.py
├── start.sh / stop.sh
└── start_web_ui.sh / stop_web_ui.sh
```
