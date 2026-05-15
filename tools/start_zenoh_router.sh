#!/usr/bin/env bash
SCRIPT_DIRECTORY="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
SOURCE_DIRECTORY="$(realpath "${SCRIPT_DIRECTORY}/..")"

source "${SOURCE_DIRECTORY}/adore.env" 2>/dev/null || true
source "/opt/ros/${ROS_DISTRO}/setup.bash" 2>/dev/null || true

LOG_DIR="${SOURCE_DIRECTORY}/.log/zenoh"
PIDFILE="${LOG_DIR}/zenoh_router.pid"
LOGFILE="${LOG_DIR}/zenoh_router.log"

mkdir -p "${LOG_DIR}"

if [ "${ZENOH_ROUTER_ENABLE:-false}" != "true" ]; then
    exit 0
fi

if [ -f "${PIDFILE}" ] && kill -0 "$(cat "${PIDFILE}")" 2>/dev/null; then
    echo "✓ Zenoh router already running (pid $(cat "${PIDFILE}"))"
    exit 0
fi

ROUTER_ARGS=""
if [ -f "${ZENOH_ROUTER_CONFIG:-}" ]; then
    ROUTER_ARGS="--zenoh-config ${ZENOH_ROUTER_CONFIG}"
fi

echo "Starting zenoh router -> ${LOGFILE}"
ros2 run rmw_zenoh_cpp rmw_zenohd ${ROUTER_ARGS} >> "${LOGFILE}" 2>&1 &
echo $! > "${PIDFILE}"
echo "  pid $!"
