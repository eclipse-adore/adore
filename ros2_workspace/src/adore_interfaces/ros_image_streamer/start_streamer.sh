#!/usr/bin/env bash
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG="${1:-$SCRIPT_DIR/config/streamer_config.yaml}"
ros2 launch ros_image_streamer streamer.launch.py config_path:="$CONFIG"
