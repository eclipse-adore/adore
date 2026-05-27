# Eclipse Zenoh Integration

The ADORe CLI bundles the ROS Zenoh bridge libraries and ROS Zenoh DDS plugin, enabling Zenoh-based communication alongside or in place of the default FastDDS transport.

## Transport Modes

ADORe supports two approaches for Zenoh transport:

**RMW Transport (rmw_zenoh_cpp)**
Configure ROS to use Zenoh as the underlying RMW implementation. This replaces FastDDS entirely and requires no bridge node.
This can be configured in the `adore.env` file.

**Bridge Node**
A ROS node that bridges selected topics between FastDDS and Zenoh, allowing both transports to coexist. The bridge node is located at:
```
ros2_workspace/src/adore_interfaces/zenoh_message_bridge
```

## Default Behavior

Both the Zenoh bridge node and a Zenoh router start automatically with the ADORe CLI. To change this, modify `adore.env`.

## Configuration

| File | Purpose |
|---|---|
| `zenoh_router_config.json5` | Zenoh router configuration |
| `zenoh_bridge_config.yaml` | Bridge node topic and connection configuration |
| `adore.env` | Startup behavior for the router and bridge services |

## Further Reading

See `ros2_workspace/src/adore_interfaces/zenoh_message_bridge/README.md` for full integration details.
