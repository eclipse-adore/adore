#!/usr/bin/env bash
# Answers, in order, for the broker named by config/bridge_config.yaml:
#
#   1. is the host reachable?
#   2. does TLS work?
#   3. does authentication work?
#   4. is there data on the broker?
#   5. does that data reach ROS?
#
# Each stage prints what it observed, including one received payload, so a
# failure identifies the layer that broke rather than just "connection failed".
#
# Usage: ./scripts/mqtt_test_remote.sh [/path/to/bridge_config.yaml]
#
# NMEA_WAIT     seconds to wait for live NMEA data (default 30)
# NMEA_REQUIRE  set to 1 to fail, rather than skip, when no NMEA data arrives
# SOLBOX_WAIT   seconds to listen for live solbox notifications (default 30)
# MOCK_WAIT     seconds to wait for our own published notification (default 15)

set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PKG_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
source "$SCRIPT_DIR/test_common.sh"

CONFIG="${1:-$PKG_ROOT/config/bridge_config.yaml}"
NMEA_TOPIC='od_imoger/vehicles/dlr1/nmea'
NMEA_ROS_TOPIC='/imoger/vehicles/dlr1/nmea'
SOLBOX_FILTER='od_imoger/solbox/+/notifications'
SOLBOX_TOPIC='od_imoger/solbox/solbox_test/notifications'
SOLBOX_ROS_TOPIC='/imoger/solbox/notifications'
NMEA_WAIT="${NMEA_WAIT:-30}"
NMEA_REQUIRE="${NMEA_REQUIRE:-0}"
SOLBOX_WAIT="${SOLBOX_WAIT:-30}"
MOCK_WAIT="${MOCK_WAIT:-15}"

if [[ ! -f "$CONFIG" ]]; then
    echo "ERROR: config not found: $CONFIG" >&2
    exit 1
fi

export MQTT_BRIDGE_CONFIG="$CONFIG"
export MQTT_BRIDGE_CERT_DIR="${MQTT_BRIDGE_CERT_DIR:-$PKG_ROOT/certs}"
export RMW_IMPLEMENTATION="${RMW_IMPLEMENTATION:-rmw_fastrtps_cpp}"
export ROS_AUTOMATIC_DISCOVERY_RANGE="${ROS_AUTOMATIC_DISCOVERY_RANGE:-LOCALHOST}"

WORK_DIR="$(mktemp -d)"
trap 'stop_bridge; rm -rf "$WORK_DIR"' EXIT

probe() {
    local stage="$1" name="$2"
    local out status
    out="$(python3 "$SCRIPT_DIR/mqtt_probe.py" --stage "$stage" --config "$CONFIG" 2>&1)"
    status=$?
    echo "  $out"
    if [[ "$status" -eq 2 ]]; then
        skip "$name" "not applicable"
        return 0
    fi
    record "$name" "$status"
    return "$status"
}

echo "=== Remote Broker Test ==="
echo "Config : $CONFIG"

# Resolving the mosquitto arguments first turns missing certificates into a skip
# rather than the hard exit mqtt_common.sh would take.
if ! python3 "$SCRIPT_DIR/bridge_mqtt_args.py" "$CONFIG" > /dev/null 2> "$WORK_DIR/args.err"; then
    echo "SKIP: cannot resolve broker settings from $CONFIG"
    sed 's/^/      /' "$WORK_DIR/args.err"
    exit 0
fi
source "$SCRIPT_DIR/mqtt_common.sh" "$CONFIG"

echo "Broker : $MQTT_HOST:$MQTT_PORT"
echo "User   : ${MQTT_USERNAME:-<anonymous>}"

banner "1. Is the host reachable?"
if ! probe tcp "host reachable ($MQTT_HOST:$MQTT_PORT)"; then
    echo "  nothing below this layer can be tested." >&2
    summary
    exit 1
fi

banner "2. Is TLS working?"
if ! probe tls "tls handshake"; then
    echo "  nothing below this layer can be tested." >&2
    summary
    exit 1
fi

banner "3. Does authentication work?"
if [[ -z "${MQTT_USERNAME:-}" || -z "${MQTT_PASSWORD:-}" ]]; then
    skip "broker authentication" "no credentials in the environment or .mqtt_secrets.env"
    summary
    exit 0
fi
if ! probe auth "broker authentication"; then
    summary
    exit 1
fi

banner "4. Is there data on the broker?"
echo "  waiting up to ${NMEA_WAIT}s for $NMEA_TOPIC"
timeout $((NMEA_WAIT + 10)) mosquitto_sub "${_broker_args[@]}" \
    -t "$NMEA_TOPIC" -C 1 -W "$NMEA_WAIT" \
    > "$WORK_DIR/nmea.log" 2> "$WORK_DIR/nmea.err"
if [[ -s "$WORK_DIR/nmea.log" ]]; then
    show_payload "nmea" "$WORK_DIR/nmea.log"
    record "live data on $NMEA_TOPIC" 0
elif [[ "$NMEA_REQUIRE" == "1" ]]; then
    record "live data on $NMEA_TOPIC" 1 "$WORK_DIR/nmea.err"
else
    skip "live data on $NMEA_TOPIC" "silent for ${NMEA_WAIT}s, vehicle is probably offline"
fi

# The solbox topic carries a live mock publisher, so a subscriber sees other
# people's traffic. Every check below correlates on action_id rather than
# taking whichever message happens to arrive first.
echo "  listening ${SOLBOX_WAIT}s on $SOLBOX_FILTER"
timeout $((SOLBOX_WAIT + 5)) mosquitto_sub "${_broker_args[@]}" \
    -t "$SOLBOX_FILTER" -W "$SOLBOX_WAIT" \
    > "$WORK_DIR/solbox_live.log" 2> "$WORK_DIR/solbox_live.err"
if show_payload "solbox" "$WORK_DIR/solbox_live.log"; then
    record "live data on $SOLBOX_FILTER" 0
    head -n 1 "$WORK_DIR/solbox_live.log" > "$WORK_DIR/solbox_first.json"
    python3 "$SCRIPT_DIR/dimos_message.py" --validate "$WORK_DIR/solbox_first.json" \
        > "$WORK_DIR/validate.log" 2>&1
    status=$?
    sed 's/^/  /' "$WORK_DIR/validate.log"
    record "notification structure is valid" "$status" "$WORK_DIR/validate.log"
else
    skip "live data on $SOLBOX_FILTER" "silent for ${SOLBOX_WAIT}s"
    skip "notification structure is valid" "no message to validate"
fi

ACTION_ID=$(( (RANDOM << 15 | RANDOM) % 900000000 + 100000000 ))
python3 "$SCRIPT_DIR/dimos_message.py" --generate --action-id "$ACTION_ID" \
    > "$WORK_DIR/mock.json"
echo "  publishing a notification to $SOLBOX_TOPIC (action_id $ACTION_ID)"

timeout $((MOCK_WAIT + 5)) mosquitto_sub "${_broker_args[@]}" \
    -t "$SOLBOX_FILTER" -W "$MOCK_WAIT" > "$WORK_DIR/solbox.log" 2>&1 &
sub_pid=$!
sleep 2
mosquitto_pub "${_broker_args[@]}" -t "$SOLBOX_TOPIC" -f "$WORK_DIR/mock.json" \
    2> "$WORK_DIR/solbox_pub.err"
pub_status=$?
wait "$sub_pid" 2>/dev/null

if [[ "$pub_status" -ne 0 ]]; then
    record "publish to $SOLBOX_TOPIC" 1 "$WORK_DIR/solbox_pub.err"
else
    record "publish to $SOLBOX_TOPIC" 0
    grep -q "$ACTION_ID" "$WORK_DIR/solbox.log"
    record "own notification returns on $SOLBOX_FILTER" $? "$WORK_DIR/solbox.log"
fi

banner "5. Does the data reach ROS?"
start_bridge "$CONFIG" "$WORK_DIR/bridge.log" 40
bridge_status=$?
if [[ "$bridge_status" -eq 2 ]]; then
    skip "data reaches ROS" "ros2 not on PATH"
elif [[ "$bridge_status" -ne 0 ]]; then
    record "bridge node connects to $MQTT_HOST:$MQTT_PORT" 1 "$WORK_DIR/bridge.log"
else
    record "bridge node connects to $MQTT_HOST:$MQTT_PORT" 0

    if [[ -s "$WORK_DIR/nmea.log" ]]; then
        timeout $((NMEA_WAIT + 10)) ros2 topic echo --once --full-length \
            "$NMEA_ROS_TOPIC" std_msgs/msg/String > "$WORK_DIR/nmea_ros.log" 2>&1
        if show_payload "nmea (ros)" "$WORK_DIR/nmea_ros.log"; then
            record "live NMEA reaches $NMEA_ROS_TOPIC" 0
        else
            record "live NMEA reaches $NMEA_ROS_TOPIC" 1 "$WORK_DIR/nmea_ros.log"
        fi
    else
        skip "live NMEA reaches $NMEA_ROS_TOPIC" "no NMEA data was seen on the broker"
    fi

    # --full-length matters: ros2 topic echo abbreviates long strings by
    # default, which truncates the JSON before action_id is visible.
    ACTION_ID=$(( (RANDOM << 15 | RANDOM) % 900000000 + 100000000 ))
    python3 "$SCRIPT_DIR/dimos_message.py" --generate --action-id "$ACTION_ID" \
        > "$WORK_DIR/mock_ros.json"
    timeout $((MOCK_WAIT + 10)) ros2 topic echo --full-length \
        "$SOLBOX_ROS_TOPIC" std_msgs/msg/String > "$WORK_DIR/ros.log" 2>&1 &
    echo_pid=$!
    sleep 3
    for _ in 1 2 3 4 5; do
        mosquitto_pub "${_broker_args[@]}" -t "$SOLBOX_TOPIC" -f "$WORK_DIR/mock_ros.json" 2>/dev/null
        sleep 2
        grep -q "$ACTION_ID" "$WORK_DIR/ros.log" && break
    done
    kill "$echo_pid" 2>/dev/null
    wait "$echo_pid" 2>/dev/null
    grep -q "$ACTION_ID" "$WORK_DIR/ros.log"
    ros_status=$?
    grep -m1 "$ACTION_ID" "$WORK_DIR/ros.log" > "$WORK_DIR/ros_match.log" 2>/dev/null
    show_payload "solbox (ros)" "$WORK_DIR/ros_match.log" || true
    record "own notification reaches $SOLBOX_ROS_TOPIC (action_id $ACTION_ID)" "$ros_status" "$WORK_DIR/ros.log"
    stop_bridge
fi

summary
