#!/usr/bin/env bash
set -e
CONFIG="${1:-}"
if [ -n "$CONFIG" ]; then
    ros2 launch ros_image_streamer viewer.launch.py config_path:="$CONFIG"
else
    ros2 launch ros_image_streamer viewer.launch.py
fi
