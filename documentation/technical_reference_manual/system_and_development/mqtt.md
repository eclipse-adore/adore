# MQTT Integration

The ADORe CLI bundles Eclipse Mosquitto and associated Python client libraries, along with a ROS bridge node for bidirectional topic bridging between ROS and MQTT.

## Bridge Node

The MQTT message bridge node is located at:
```
ros2_workspace/src/adore_interfaces/mqtt_message_bridge
```

It subscribes and publishes to configured ROS topics, forwarding messages to and from an MQTT broker. The broker can be a remote instance or a local one managed by the CLI.

## Default Behavior

The bridge node and optional MQTT broker do not start automatically by default. Both are enabled via `adore.env`.

## Configuration

| File | Purpose |
|---|---|
| `mqtt_bridge_config.yaml` | Define which ROS topics to bridge and their MQTT mappings |
| `adore.env` | Enable the bridge and broker services at startup; configure remote broker connection parameters (host, port, credentials) |

## Further Reading

See `ros2_workspace/src/adore_interfaces/mqtt_message_bridge/README.md` for full integration details.
