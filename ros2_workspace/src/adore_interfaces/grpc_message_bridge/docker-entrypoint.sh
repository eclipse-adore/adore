#!/bin/bash
set -e

source /opt/ros/${ROS_DISTRO}/setup.bash
source /ros2_ws/install/setup.bash

exec ros2 run grpc_message_bridge bridge_node \
    --ros-args \
    -p config_path:="${BRIDGE_CONFIG_PATH:-/ros2_ws/install/grpc_message_bridge/share/grpc_message_bridge/config/bridge_config.yaml}" \
    -p grpc_host:="${GRPC_HOST:-0.0.0.0}" \
    -p grpc_port:="${GRPC_PORT:-50051}"
