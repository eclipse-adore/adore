#!/bin/bash
set -e
source /opt/ros/${ROS_DISTRO}/setup.bash
source /ws/install/setup.bash

# If arguments are passed, run them directly instead of the bridge node.
# This allows: docker run ... python3 scripts/test_integration.py
if [ $# -gt 0 ]; then
    exec "$@"
fi

exec ros2 run grpc_message_bridge bridge_node \
    --ros-args \
    -p config_path:=${BRIDGE_CONFIG_PATH:-/config/bridge_config.yaml} \
    -p grpc_host:=${GRPC_HOST:-0.0.0.0} \
    -p grpc_port:=${GRPC_PORT:-50051}
