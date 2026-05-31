#!/usr/bin/env bash
SCRIPT_DIRECTORY="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
export SOURCE_DIRECTORY="$(realpath "${SCRIPT_DIRECTORY}/..")"

source "${SOURCE_DIRECTORY}/adore.env"
source "/opt/ros/${ROS_DISTRO}/setup.bash" 2>/dev/null || true

ROS2_WORKSPACE_DIRECTORY="${SOURCE_DIRECTORY}/ros2_workspace"
if [ -f "${ROS2_WORKSPACE_DIRECTORY}/install/local_setup.bash" ]; then
    source "${ROS2_WORKSPACE_DIRECTORY}/install/local_setup.bash"
fi

LOG_DIR="${SOURCE_DIRECTORY}/.log/zenoh"
PIDFILE="${LOG_DIR}/zenoh_bridge.pid"
LOGFILE="${LOG_DIR}/zenoh_bridge.log"

mkdir -p "${LOG_DIR}"

if [ "${ZENOH_BRIDGE_ENABLE:-false}" != "true" ]; then
    exit 0
fi

if [ -f "${PIDFILE}" ] && kill -0 "$(cat "${PIDFILE}")" 2>/dev/null; then
    echo "✓ Zenoh bridge already running (pid $(cat "${PIDFILE}"))"
    exit 0
fi

ZENOH_CONFIG_ARG=""
if [ -f "${ZENOH_BRIDGE_CONFIG:-}" ]; then
    ZENOH_CONFIG_ARG="zenoh_config_path:=${ZENOH_BRIDGE_CONFIG}"
fi

echo "Starting zenoh_message_bridge -> ${LOGFILE}"
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
ros2 launch zenoh_message_bridge bridge.launch.py \
    zenoh_router:="${ZENOH_BRIDGE_ROUTER:-tcp/localhost:7447}" \
    ${ZENOH_CONFIG_ARG} \
    >> "${LOGFILE}" 2>&1 &
BRIDGE_PID=$!
echo $BRIDGE_PID > "${PIDFILE}"
echo "  pid ${BRIDGE_PID}"
