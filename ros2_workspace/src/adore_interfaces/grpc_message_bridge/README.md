# grpc_message_bridge

## Setup

```bash
cp .secrets.env.template .secrets.env
# fill in CLIENT_SECRET
make build
```

## Run

```bash
make start
make stop
make restart
make logs
```

## Inspect live data

Subscribe and pretty-print incoming messages from the supervision backend.

```bash
# All message types, 30s (default)
make inspect

# Telemetry only, 60s
make inspect TYPE=TELEMETRY DURATION=60

# Notifications only, 120s
make inspect TYPE=NOTIFICATIONS DURATION=120

# All types, specific vehicles
make inspect TYPE=ALL VEHICLE="MV-001 MV-002"

# Combine
make inspect TYPE=TELEMETRY DURATION=300 VEHICLE=MV-001
```

`TYPE` options: `ALL` (default) · `TELEMETRY` · `NOTIFICATIONS`

## Test

```bash
# All 7 scenarios
make test

# Single scenario
make test SCENARIO=4
```

## ROS topics

All messages are JSON strings on `std_msgs/msg/String`.

### Incoming (supervision backend → ROS)

| Topic | Content |
|---|---|
| `/supervision/telemetry` | `VehicleTelemetryUpdate` -- vehicle id, state, position, velocity, battery, obstacles |
| `/supervision/notifications` | `NotificationMessage` -- id, vehicle id, type, severity, title, message |
| `/supervision/ack/rx` | `Ack` -- success, error_msg |
| `/supervision/signaling/rx` | `SignalMessage` -- WebRTC signaling (offer/answer/ICE) |

### Outgoing (ROS → supervision backend)

| Topic | Content |
|---|---|
| `/supervision/subscription` | `SubscriptionRequest` -- type (TELEMETRY/NOTIFICATIONS/ALL), vehicle_ids |
| `/supervision/ack/tx` | `Ack` |
| `/supervision/signaling/tx` | `SignalMessage` |

### Examples

Subscribe to telemetry:
```bash
ros2 topic echo /supervision/telemetry
```

Subscribe to notifications:
```bash
ros2 topic echo /supervision/notifications
```

Send a subscription request (all vehicles, telemetry only):
```bash
ros2 topic pub --once /supervision/subscription std_msgs/msg/String \
  '{"data": "{\"type\": \"TELEMETRY\", \"vehicleIds\": []}"}'
```

Send a subscription request filtered to specific vehicles:
```bash
ros2 topic pub --once /supervision/subscription std_msgs/msg/String \
  '{"data": "{\"type\": \"ALL\", \"vehicleIds\": [\"MV-001\", \"MV-002\"]}"}'
```

List all active bridge topics:
```bash
ros2 topic list | grep supervision
```

Check message rate:
```bash
ros2 topic hz /supervision/telemetry
```
