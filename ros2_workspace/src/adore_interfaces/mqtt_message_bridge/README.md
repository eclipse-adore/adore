# mqtt_message_bridge

ROS 2 bridge node that forwards messages between ROS 2 topics and an MQTT broker. Serialization is CDR via `rclpy.serialization`.

## Dependencies

```
pip3 install -r requirements.pip3
```

## Configuration

Edit `config/bridge_config.yaml`:

```yaml
ros2_to_mqtt:
  - ros_topic: "/ros2_chatter"
    mqtt_topic: "ros2/chatter"
    msg_type: "std_msgs/msg/String"

mqtt_to_ros2:
  - mqtt_topic: "mqtt/chatter"
    ros_topic: "/mqtt_chatter"
    msg_type: "std_msgs/msg/String"
```

Each mapping supports optional QoS overrides: `qos_depth`, `qos_durability` (`volatile`|`transient_local`), `qos_reliability` (`best_effort`|`reliable`).

## Launch

```bash
ros2 launch mqtt_message_bridge bridge.launch.py mqtt_broker:=localhost mqtt_port:=1883
```

## Test

```bash
python3 mqtt_publish.py    # publishes to mqtt/chatter
python3 mqtt_subscribe.py  # subscribes to mqtt/chatter
ros2 topic echo /mqtt_chatter
```

`mqtt_publish.py` and `mqtt_subscribe.py` respect `MQTT_BROKER_HOST` and `MQTT_BROKER_PORT` environment variables.
