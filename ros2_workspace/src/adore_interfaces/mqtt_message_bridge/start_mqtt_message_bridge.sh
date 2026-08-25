#!/usr/bin/env bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export MQTT_BRIDGE_CERT_DIR="${MQTT_BRIDGE_CERT_DIR:-$SCRIPT_DIR/certs}"
RMW_IMPLEMENTATION=rmw_fastrtps_cpp ros2 launch mqtt_message_bridge bridge.launch.py
