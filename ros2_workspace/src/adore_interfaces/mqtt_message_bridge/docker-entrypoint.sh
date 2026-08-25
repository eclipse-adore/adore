#!/usr/bin/env bash
set -e

source "/opt/ros/${ROS_DISTRO}/setup.bash"
source /ws/install/setup.bash

SRC=/ws/src/mqtt_message_bridge

case "${1:-bridge}" in
    bridge)
        shift || true
        exec ros2 launch mqtt_message_bridge bridge.launch.py "$@"
        ;;
    test)
        shift || true
        exec "$SRC/scripts/run_tests.sh" "$@"
        ;;
    shell)
        exec bash
        ;;
    *)
        exec "$@"
        ;;
esac
