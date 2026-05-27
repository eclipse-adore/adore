#!/usr/bin/env bash
set -e
TOPIC="${1:-/camera/image_raw}"
WINDOW="${2:-ROS Image Viewer}"
ros2 launch ros_image_streamer viewer.launch.py topic:="$TOPIC" window_name:="$WINDOW"
