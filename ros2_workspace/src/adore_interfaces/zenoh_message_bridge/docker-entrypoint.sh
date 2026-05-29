#!/bin/bash
set -e

source /opt/ros/${ROS_DISTRO}/setup.bash
source /ros2_ws/install/setup.bash

exec ros2 run zenoh_message_bridge bridge_node \
    --ros-args \
    -p config_path:="${BRIDGE_CONFIG_PATH:-/ros2_ws/install/zenoh_message_bridge/share/zenoh_message_bridge/config/bridge_config.yaml}" \
    -p zenoh_config_path:="${ZENOH_CONFIG_PATH:-/ros2_ws/zenoh_bridge_config.json5}" \
    -p zenoh_router:="${ZENOH_ROUTER:-tcp/localhost:7447}"
