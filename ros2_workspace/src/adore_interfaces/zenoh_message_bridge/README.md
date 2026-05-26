# zenoh_message_bridge

ROS 2 bridge node that forwards messages between ROS 2 topics and a Zenoh keyspace. Serialization is CDR via `rclpy.serialization`.

## Dependencies

```
pip3 install -r requirements.pip3
```

## Configuration

Edit `config/bridge_config.yaml`:

```yaml
ros2_to_zenoh:
  - ros_topic: "/ros2_chatter"
    zenoh_key: "0/ros2_chatter/**"
    msg_type: "std_msgs/msg/String"

zenoh_to_ros2:
  - zenoh_key: "0/zenoh_chatter/**"
    ros_topic: "/zenoh_chatter"
    msg_type: "std_msgs/msg/String"
```

Each mapping supports optional QoS overrides: `qos_depth`, `qos_durability` (`volatile`|`transient_local`), `qos_reliability` (`best_effort`|`reliable`).

## Launch

```bash
ros2 launch zenoh_message_bridge bridge.launch.py zenoh_router:=tcp/localhost:7447
```

## Test

```bash
python3 zenoh_publish.py   # publishes to zenoh/chatter
python3 zenoh_echo.py      # subscribes to zenoh/chatter
ros2 topic echo /zenoh_chatter
```
