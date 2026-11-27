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

A `ros2_to_mqtt` topic may contain `{field}` placeholders, filled per message from
the top-level field of the same name in the JSON payload. This requires
`format: raw`. Messages without a usable field are dropped.

```yaml
ros2_to_mqtt:
  - ros_topic: "/device/request"
    mqtt_topic: "{region}/{device_id}/request"
    msg_type: "std_msgs/msg/String"
    format: raw
```

`mqtt_to_ros2` topics take the usual MQTT wildcards `+` and `#`. They may also
contain placeholders. The bridge subscribes with `+` in their place and adds the
matched levels to the JSON payload. This also requires `format: raw`.
Fields the payload already holds are kept, a differing value is logged.

```yaml
mqtt_to_ros2:
  - mqtt_topic: "{region}/{device_id}/response/request_status"
    ros_topic: "/response/request_status"
    msg_type: "std_msgs/msg/String"
    format: raw
```

On `region-A/id-12345/response/request_status`, `{"vehicle_id": "0"}` arrives in ROS as
`{"vehicle_id": "0", "region": "region-A", "device_id": "id-12345"}`.


## Launch

```bash
ros2 launch mqtt_message_bridge bridge.launch.py config_path:=/path/to/bridge_config.yaml
```

Without `config_path` the bridge takes `config/bridge_config.yaml`, a local broker
without TLS or credentials.

## Test

```bash
make build         # docker image
make test          # local suite broker
make clean
```

`./scripts/run_tests.sh --remote PATH` adds the remote suite for the broker in
the config at PATH. A failure names the layer that broke:

1. host reachable (TCP)
2. TLS handshake, reporting the negotiated version and the server certificate
3. authentication, reporting the CONNACK reason code

Stages below a failure are not attempted. Missing credentials or certificates
skip rather than fail.

Individually, against whatever broker `config/bridge_config.yaml` names:

```bash
./scripts/mqtt_check_broker.sh
./scripts/mqtt_test_pubsub.sh
python3 scripts/mqtt_publish.py mqtt/chatter
python3 scripts/mqtt_subscribe.py mqtt/chatter
```

The scripts read the same config as the node, so TLS and credentials are picked
up automatically. `MQTT_HOST`, `MQTT_PORT`, `MQTT_TLS`, `MQTT_USERNAME` and
`MQTT_PASSWORD` override the file. `--format raw` skips the CDR layer and works
without a sourced ROS workspace.
