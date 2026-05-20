#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_FILE="${SCRIPT_DIR}/.hardware_monitor.pid"

if [[ -f "${PID_FILE}" ]]; then
    EXISTING_PID=$(cat "${PID_FILE}")
    if kill -0 "${EXISTING_PID}" 2>/dev/null; then
        echo "hardware_monitor is already running (PID ${EXISTING_PID})"
        exit 0
    else
        rm -f "${PID_FILE}"
    fi
fi

if [[ -z "${ROS_DISTRO:-}" ]]; then
    echo "ERROR: ROS 2 environment not sourced. Source /opt/ros/<distro>/setup.bash first."
    exit 1
fi

# ROS 2 log directory resolution matches the RCL convention:
#   ROS_LOG_DIR > ROS_HOME/log > ~/.ros/log
ROS_HOME_DEFAULT="${HOME}/.ros"
ROS_LOG_BASE="${ROS_LOG_DIR:-${ROS_HOME:-${ROS_HOME_DEFAULT}}/log}"
mkdir -p "${ROS_LOG_BASE}"
LAUNCH_LOG="${ROS_LOG_BASE}/hardware_monitor_launch_$(date +%Y%m%d_%H%M%S).log"

echo "Starting hardware_monitor nodes..."
ros2 launch hardware_monitor hardware_monitor.launch.py \
    > "${LAUNCH_LOG}" 2>&1 &

LAUNCH_PID=$!
echo "${LAUNCH_PID}" > "${PID_FILE}"
echo "hardware_monitor started (PID ${LAUNCH_PID})"
echo "Launch stdout/stderr: ${LAUNCH_LOG}"
echo "Node logs: ${ROS_LOG_BASE}/latest/"
