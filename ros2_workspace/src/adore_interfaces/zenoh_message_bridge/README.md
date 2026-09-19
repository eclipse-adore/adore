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

Each mapping accepts optional overrides: `format` (`cdr` | `json` | `cdr_json`), `domain_id`, `zenoh_key`, `qos_depth`, `qos_reliability` (`reliable` | `best_effort`), `qos_durability` (`volatile` | `transient_local`).

`zenoh_key` replaces the derived key expression, which is `<domain_id>/<topic>/<dds_type>/<type_hash>`
for publishing and `<domain_id>/<topic>/<dds_type>/*` for subscribing. Use it when the peer is not a
ROS node. It makes `domain_id` irrelevant for that mapping and suppresses the liveliness token on
`ros2_to_zenoh`.

Top-level keys: `ros_domain_id`, `zenoh_bridge_id`, `rmw_target` (`humble` | `jazzy`).

### Multiple config files

`config_paths` takes a comma separated list of files and merges them in order.

```bash
ros2 launch zenoh_message_bridge bridge.launch.py \
    config_paths:=/opt/site/vehicles.yaml,/opt/site/services.yaml
```

Mappings from all files are concatenated. Top-level keys are taken from the first file that sets
them, so put `ros_domain_id`, `zenoh_bridge_id` and `rmw_target` in the first file. 

`config_paths` takes precedence over `config_path` when both are given.

## Build

```bash
colcon build --packages-select zenoh_message_bridge
source install/setup.bash
```

## Launch

```bash
ros2 launch zenoh_message_bridge bridge.launch.py zenoh_router:=tcp/localhost:7447
```

Launch arguments: `config_path`, `config_paths`, `zenoh_router`, `zenoh_config_path`.

## Test

```bash
zenohd --config zenoh_router_config.json5

ros2 launch zenoh_message_bridge bridge.launch.py \
    config_path:=$(ros2 pkg prefix --share zenoh_message_bridge)/test/bridge_config.test.yaml \
    zenoh_config_path:=zenoh_bridge_config.json5
```

Zenoh to ROS 2:

```bash
python3 zenoh_publish.py                                 # json
ros2 topic echo /test/json_in

python3 zenoh_publish.py --key test/cdr_in --format cdr  # cdr
ros2 topic echo /test/cdr_in
```

ROS 2 to zenoh:

```bash
ros2 topic pub /test/json_out std_msgs/msg/String "{data: 'hi'}"
python3 zenoh_echo.py                                    # json

ros2 topic pub /test/cdr_out std_msgs/msg/String "{data: 'hi'}"
python3 zenoh_echo.py --key test/cdr_out --format cdr    # cdr
```

Use `zenoh_echo.py --format raw` to print the bytes.
