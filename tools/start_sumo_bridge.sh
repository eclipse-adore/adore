#!/usr/bin/env bash
set -eo pipefail
SCRIPT_DIRECTORY="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
export SOURCE_DIRECTORY="$(realpath "${SCRIPT_DIRECTORY}/..")"
source "${SOURCE_DIRECTORY}/adore.env"
source "/opt/ros/${ROS_DISTRO}/setup.bash" 2>/dev/null || true
ROS2_WORKSPACE_DIRECTORY="${SOURCE_DIRECTORY}/ros2_workspace"
if [ -f "${ROS2_WORKSPACE_DIRECTORY}/install/local_setup.bash" ]; then
    source "${ROS2_WORKSPACE_DIRECTORY}/install/local_setup.bash"
fi
LOG_DIR="${SOURCE_DIRECTORY}/.log/sumo_bridge"
PIDFILE="${LOG_DIR}/sumo_bridge.pid"
LOGFILE="${LOG_DIR}/sumo_bridge.log"
mkdir -p "${LOG_DIR}"
if [ "${SUMO_BRIDGE_ENABLE:-false}" != "true" ]; then
    exit 0
fi
if [ -f "${PIDFILE}" ] && kill -0 "$(cat "${PIDFILE}")" 2>/dev/null; then
    echo "✓ sumo_bridge already running (pid $(cat "${PIDFILE}"))"
    exit 0
fi
echo "Starting sumo_bridge -> ${LOGFILE}"
ros2 run sumo_bridge sumo_bridge --ros-args \
    --param "sumo_config_file:=${SOURCE_DIRECTORY}/${SUMO_CONFIG_DIRECTORY}/${SUMO_CONFIG_FILE}" \
    >> "${LOGFILE}" 2>&1 &
BRIDGE_PID=$!
echo $BRIDGE_PID > "${PIDFILE}"
echo "  pid ${BRIDGE_PID}"
