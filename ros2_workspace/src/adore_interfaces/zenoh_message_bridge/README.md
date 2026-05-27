# zenoh_message_bridge

ROS 2 bridge node that forwards messages between ROS 2 DDS topics and a Zenoh keyspace using CDR serialization via `rclpy.serialization`.

## Dependencies

```bash
pip3 install -r requirements.pip3
```

## Configuration

Edit `config/bridge_config.yaml`.

**ROS 2 to Zenoh:**
```yaml
ros2_to_zenoh:
  - ros_topic: "/ros2_chatter"
    msg_type: "std_msgs/msg/String"
```

**Zenoh to ROS 2:**
```yaml
zenoh_to_ros2:
  - ros_topic: "/zenoh_chatter"
    msg_type: "std_msgs/msg/String"
```

Each mapping accepts optional overrides: `format` (`cdr` | `json` | `cdr_json`), `domain_id`, `qos_depth`, `qos_reliability` (`reliable` | `best_effort`), `qos_durability` (`volatile` | `transient_local`).

Top-level keys: `ros_domain_id`, `zenoh_bridge_id`, `rmw_target` (`humble` | `jazzy`).

## Build

```bash
colcon build --packages-select zenoh_message_bridge
source install/setup.bash
```

## Launch

```bash
ros2 launch zenoh_message_bridge bridge.launch.py zenoh_router:=tcp/localhost:7447
```

## Test

```bash
python3 zenoh_publish.py    # publish to Zenoh
python3 zenoh_echo.py       # subscribe on Zenoh
ros2 topic echo /zenoh_chatter
```
