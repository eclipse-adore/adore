#!/usr/bin/env bash
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG="${1:-$SCRIPT_DIR/config/weather_service_config.yaml}"
ros2 launch weather_service_interface weather_service.launch.py config_path:="$CONFIG"
