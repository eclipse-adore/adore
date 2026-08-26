#!/usr/bin/env bash
# End-to-end test run against a throwaway local broker.
#
# Runs the local suite against a throwaway broker, then the remote suite against
# the broker in config/bridge_config.yaml.
#
# Usage: ./scripts/run_tests.sh [--no-broker] [--config PATH] [--no-remote]
#
# --no-broker  skip starting mosquitto and use the broker the config names
# --config     test against a different bridge config (implies a real broker)
# --no-remote  skip the remote broker suite

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PKG_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

source "$SCRIPT_DIR/test_common.sh"

START_BROKER=1
RUN_REMOTE=1
CONFIG="$PKG_ROOT/test/bridge_config.test.yaml"
REMOTE_CONFIG="${REMOTE_CONFIG:-$PKG_ROOT/config/bridge_config.yaml}"

while [[ $# -gt 0 ]]; do
    case "$1" in
        --no-broker) START_BROKER=0; shift ;;
        --config)    CONFIG="$2"; START_BROKER=0; shift 2 ;;
        --remote)    RUN_REMOTE=1; shift ;;
        --no-remote) RUN_REMOTE=0; shift ;;
        *) echo "unknown argument: $1" >&2; exit 2 ;;
    esac
done

if [[ ! -f "$CONFIG" ]]; then
    echo "ERROR: config not found: $CONFIG" >&2
    exit 1
fi

# Deliberately not inherited: the ambient value points at the production broker.
export MQTT_BRIDGE_CONFIG="$CONFIG"
export MQTT_BRIDGE_CERT_DIR="${MQTT_BRIDGE_CERT_DIR:-$PKG_ROOT/certs}"
export RMW_IMPLEMENTATION="${RMW_IMPLEMENTATION:-rmw_fastrtps_cpp}"
export ROS_AUTOMATIC_DISCOVERY_RANGE="${ROS_AUTOMATIC_DISCOVERY_RANGE:-LOCALHOST}"
export ROS_DOMAIN_ID="${ROS_DOMAIN_ID:-42}"
export PYTHONUNBUFFERED=1
unset MQTT_HOST MQTT_PORT MQTT_TLS MQTT_USERNAME MQTT_PASSWORD \
      MQTT_CA_CERT MQTT_CLIENT_CERT MQTT_CLIENT_KEY

WORK_DIR="$(mktemp -d)"
BROKER_PID=""

cleanup() {
    stop_bridge
    [[ -n "$BROKER_PID" ]] && kill "$BROKER_PID" 2>/dev/null
    wait 2>/dev/null
    rm -rf "$WORK_DIR"
}
trap cleanup EXIT

start_broker() {
    cat > "$WORK_DIR/mosquitto.conf" <<'EOF'
listener 1883 127.0.0.1
allow_anonymous true
persistence false
EOF
    mosquitto -c "$WORK_DIR/mosquitto.conf" > "$WORK_DIR/mosquitto.log" 2>&1 &
    BROKER_PID=$!
    if ! wait_for_port 127.0.0.1 1883; then
        echo "ERROR: local mosquitto did not come up" >&2
        cat "$WORK_DIR/mosquitto.log" >&2
        exit 1
    fi
    echo "local broker running on 127.0.0.1:1883 (pid $BROKER_PID)"
}

banner "Unit tests"
( cd "$PKG_ROOT" && python3 -m unittest discover -s test -t "$PKG_ROOT" -v ) \
    > "$WORK_DIR/unit.log" 2>&1
record "unit tests" $? "$WORK_DIR/unit.log"

if [[ "$START_BROKER" -eq 1 ]]; then
    banner "Local broker"
    start_broker
fi

banner "Broker reachability"
"$SCRIPT_DIR/mqtt_check_broker.sh" "$MQTT_BRIDGE_CONFIG" > "$WORK_DIR/check.log" 2>&1
record "mqtt_check_broker.sh" $? "$WORK_DIR/check.log"

banner "mosquitto round trip"
"$SCRIPT_DIR/mqtt_test_pubsub.sh" "$MQTT_BRIDGE_CONFIG" > "$WORK_DIR/pubsub.log" 2>&1
record "mqtt_test_pubsub.sh" $? "$WORK_DIR/pubsub.log"

banner "Python script round trip"
expected="script-round-trip-$$"
python3 "$SCRIPT_DIR/mqtt_subscribe.py" test/scripts --count 1 --format raw \
    > "$WORK_DIR/sub.log" 2>&1 &
sub_pid=$!
sleep 3
python3 "$SCRIPT_DIR/mqtt_publish.py" test/scripts --count 3 --interval 0.5 \
    --format raw --message "$expected" > "$WORK_DIR/pub.log" 2>&1
pub_status=$?
wait "$sub_pid" 2>/dev/null
if [[ "$pub_status" -eq 0 ]] && grep -q "$expected" "$WORK_DIR/sub.log"; then
    record "mqtt_publish.py -> mqtt_subscribe.py" 0
else
    cat "$WORK_DIR/pub.log" >> "$WORK_DIR/sub.log"
    record "mqtt_publish.py -> mqtt_subscribe.py" 1 "$WORK_DIR/sub.log"
fi

banner "Diagnostics on an unreachable broker"
MQTT_HOST=127.0.0.1 MQTT_PORT=1 timeout 30 python3 "$SCRIPT_DIR/mqtt_subscribe.py" \
    test/unreachable --format raw > "$WORK_DIR/unreachable.log" 2>&1
status=$?
if [[ "$status" -eq 1 ]] && grep -q '127.0.0.1:1' "$WORK_DIR/unreachable.log"; then
    record "connection failure reports host and port" 0
else
    record "connection failure reports host and port" 1 "$WORK_DIR/unreachable.log"
fi

banner "Bridge node"
bridge_status=3
if [[ "$START_BROKER" -eq 0 ]]; then
    skip "bridge node round trip" "needs the local broker"
else
    start_bridge "$MQTT_BRIDGE_CONFIG" "$WORK_DIR/bridge.log"
    bridge_status=$?
fi

if [[ "$bridge_status" -eq 2 ]]; then
    skip "bridge node round trip" "ros2 not on PATH"
elif [[ "$bridge_status" -eq 0 ]]; then
    record "bridge node connects" 0

    payload="ros-to-mqtt-$$"
    mosquitto_sub -h 127.0.0.1 -p 1883 -t test/outbound -C 1 -W 15 \
        > "$WORK_DIR/r2m.log" 2>&1 &
    sub_pid=$!
    sleep 1
    ros2 topic pub -r 2 /test/outbound std_msgs/msg/String "{data: '$payload'}" \
        > "$WORK_DIR/r2m_pub.log" 2>&1 &
    pub_pid=$!
    wait "$sub_pid" 2>/dev/null
    kill "$pub_pid" 2>/dev/null
    wait "$pub_pid" 2>/dev/null
    grep -q "$payload" "$WORK_DIR/r2m.log"
    record "ros2 -> mqtt (/test/outbound)" $? "$WORK_DIR/r2m.log"

    timeout 20 ros2 topic echo --once /test/inbound std_msgs/msg/String \
        > "$WORK_DIR/m2r.log" 2>&1 &
    echo_pid=$!
    sleep 3
    payload="mqtt-to-ros-$$"
    for _ in 1 2 3; do
        mosquitto_pub -h 127.0.0.1 -p 1883 -t test/inbound -m "$payload"
        sleep 1
        kill -0 "$echo_pid" 2>/dev/null || break
    done
    wait "$echo_pid" 2>/dev/null
    grep -q "$payload" "$WORK_DIR/m2r.log"
    record "mqtt -> ros2 (/test/inbound)" $? "$WORK_DIR/m2r.log"

    timeout 20 ros2 topic echo --once /test/wildcard std_msgs/msg/String \
        > "$WORK_DIR/wild.log" 2>&1 &
    echo_pid=$!
    sleep 3
    payload="wildcard-$$"
    for _ in 1 2 3; do
        mosquitto_pub -h 127.0.0.1 -p 1883 -t test/wildcard/unit0/data -m "$payload"
        sleep 1
        kill -0 "$echo_pid" 2>/dev/null || break
    done
    wait "$echo_pid" 2>/dev/null
    grep -q "$payload" "$WORK_DIR/wild.log"
    record "mqtt wildcard -> ros2 (/test/wildcard)" $? "$WORK_DIR/wild.log"

    stop_bridge
elif [[ "$bridge_status" -eq 1 ]]; then
    record "bridge node connects" 1 "$WORK_DIR/bridge.log"
fi

banner "Configured topic loopback"
"$SCRIPT_DIR/mqtt_test_bridge.sh" "$MQTT_BRIDGE_CONFIG" "$MQTT_BRIDGE_CONFIG" \
    > "$WORK_DIR/topics.log" 2>&1
record "mqtt_test_bridge.sh" $? "$WORK_DIR/topics.log"

if [[ "$RUN_REMOTE" -eq 1 ]]; then
    printf '\n########## Remote broker suite ##########\n'
    RESULTS_FILE="$WORK_DIR/remote.results" "$SCRIPT_DIR/mqtt_test_remote.sh" "$REMOTE_CONFIG"
    absorb_results "$WORK_DIR/remote.results"
    printf '########## End remote broker suite ##########\n'
else
    skip "remote broker suite" "--no-remote"
fi

summary
