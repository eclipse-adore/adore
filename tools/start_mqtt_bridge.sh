#!/usr/bin/env bash
SCRIPT_DIRECTORY="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
export SOURCE_DIRECTORY="$(realpath "${SCRIPT_DIRECTORY}/..")"

source "${SOURCE_DIRECTORY}/adore.env"
source "/opt/ros/${ROS_DISTRO}/setup.bash" 2>/dev/null || true

ROS2_WORKSPACE_DIRECTORY="${SOURCE_DIRECTORY}/ros2_workspace"
if [ -f "${ROS2_WORKSPACE_DIRECTORY}/install/local_setup.bash" ]; then
    source "${ROS2_WORKSPACE_DIRECTORY}/install/local_setup.bash"
fi

LOG_DIR="${SOURCE_DIRECTORY}/.log/mqtt"
PIDFILE="${LOG_DIR}/mqtt_bridge.pid"
LOGFILE="${LOG_DIR}/mqtt_bridge.log"

mkdir -p "${LOG_DIR}"

if [ "${MQTT_BRIDGE_ENABLE:-false}" != "true" ]; then
    exit 0
fi

if [ -f "${PIDFILE}" ] && kill -0 "$(cat "${PIDFILE}")" 2>/dev/null; then
    echo "✓ MQTT bridge already running (pid $(cat "${PIDFILE}"))"
    exit 0
fi

echo "Starting mqtt_message_bridge -> ${LOGFILE}"
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
ros2 launch mqtt_message_bridge bridge.launch.py \
    config_path:="${MQTT_BRIDGE_CONFIG}" \
    >> "${LOGFILE}" 2>&1 &
BRIDGE_PID=$!
echo $BRIDGE_PID > "${PIDFILE}"
echo "  pid ${BRIDGE_PID}"
