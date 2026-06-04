#!/usr/bin/env bash
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG="${1:-$SCRIPT_DIR/config/weather_service_config.yaml}"

ros2 launch weather_service_interface weather_service.launch.py config_path:="$CONFIG" \
    > /tmp/weather_service.log 2>&1 &
SERVICE_PID=$!

cleanup() {
    kill "$SERVICE_PID" 2>/dev/null || true
    wait "$SERVICE_PID" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

"$SCRIPT_DIR/start_visualizer.sh" "$CONFIG"
