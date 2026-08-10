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

## DiMOS 5.2 interface

`config/bridge_config.yaml` targets the UseCase 5.2 broker
(`mqtts://broker-imoger.dev.dimos-ops.com:8887`, MQTT v3.1.1, QoS 1) using the
certificate file names the specification hands out: `imoger-rootCA.crt`,
`dlr-client.crt`, `dlr-client.key`. Credentials come from `.mqtt_secrets.env`.

Subscribed topics:

| MQTT | ROS 2 |
| --- | --- |
| `od_imoger/solbox/+/notifications` | `/imoger/solbox/notifications` |
| `od_imoger/vehicles/dlr1/nmea` | `/imoger/vehicles/dlr1/nmea` |

Payloads are UTF-8 JSON and are bridged verbatim (`format: raw`) into
`std_msgs/msg/String`. `scripts/dimos_message.py` builds a notification message
and checks a received one for the fields the bridge relies on. It validates
structure and types only; field values are left to the publisher, since the live
traffic uses cause codes, station types and intervals outside any fixed list.

## Launch

```bash
ros2 launch mqtt_message_bridge bridge.launch.py mqtt_broker:=localhost mqtt_port:=1883
```

## Test

```bash
make build         # docker image
make test          # local suite, then the remote broker suite
make test-offline  # local suite only
make clean
```

The remote suite works down the stack against the broker in
`config/bridge_config.yaml`, so a failure names the layer that broke:

1. host reachable (TCP)
2. TLS handshake, reporting the negotiated version and the server certificate
3. authentication, reporting the CONNACK reason code
4. live data on `od_imoger/vehicles/dlr1/nmea`, plus a synthetic notification
   published to `od_imoger/solbox/solbox_test/notifications`
5. the same data arriving on `/imoger/vehicles/dlr1/nmea` and
   `/imoger/solbox/notifications` through the bridge

One received payload is printed at each stage. Stages below a failure are not
attempted. Missing credentials or certificates skip rather than fail. `NMEA_WAIT`
allows longer for live data; `NMEA_REQUIRE=0` treats a silent vehicle as a skip.

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
