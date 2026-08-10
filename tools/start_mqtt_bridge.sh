#!/usr/bin/env bash
SCRIPT_DIRECTORY="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
export SOURCE_DIRECTORY="$(realpath "${SCRIPT_DIRECTORY}/..")"

source "${SOURCE_DIRECTORY}/adore.env"
source "/opt/ros/${ROS_DISTRO}/setup.bash" 2>/dev/null || true

ROS2_WORKSPACE_DIRECTORY="${SOURCE_DIRECTORY}/ros2_workspace"
if [ -f "${ROS2_WORKSPACE_DIRECTORY}/install/local_setup.bash" ]; then
    source "${ROS2_WORKSPACE_DIRECTORY}/install/local_setup.bash"
fi

PACKAGE_DIRECTORY="${MQTT_BRIDGE_PACKAGE_DIR:-${ROS2_WORKSPACE_DIRECTORY}/src/adore_interfaces/mqtt_message_bridge}"
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

# The config moved from <package>/bridge_config.yaml to <package>/config/.
DEFAULT_CONFIG="${PACKAGE_DIRECTORY}/config/bridge_config.yaml"
if [ -z "${MQTT_BRIDGE_CONFIG:-}" ]; then
    MQTT_BRIDGE_CONFIG="${DEFAULT_CONFIG}"
elif [ ! -f "${MQTT_BRIDGE_CONFIG}" ]; then
    RELOCATED="$(dirname "${MQTT_BRIDGE_CONFIG}")/config/$(basename "${MQTT_BRIDGE_CONFIG}")"
    if [ -f "${RELOCATED}" ]; then
        echo "Note: MQTT_BRIDGE_CONFIG points at the old location; using ${RELOCATED}"
        echo "      update adore.env to avoid this fallback."
        MQTT_BRIDGE_CONFIG="${RELOCATED}"
    fi
fi
export MQTT_BRIDGE_CONFIG

if [ ! -f "${MQTT_BRIDGE_CONFIG}" ]; then
    echo "Error: bridge config not found: ${MQTT_BRIDGE_CONFIG}"
    echo "       expected ${DEFAULT_CONFIG}"
    echo "       set MQTT_BRIDGE_CONFIG or MQTT_BRIDGE_PACKAGE_DIR in adore.env"
    exit 1
fi

# Certificates and .mqtt_secrets.env live in the source tree and are read
# relative to it, so both must be pinned when launching from the install space.
export MQTT_BRIDGE_CERT_DIR="${MQTT_BRIDGE_CERT_DIR:-${PACKAGE_DIRECTORY}/certs}"

echo "Starting mqtt_message_bridge -> ${LOGFILE}"
echo "  config ${MQTT_BRIDGE_CONFIG}"
echo "  certs  ${MQTT_BRIDGE_CERT_DIR}"
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
ros2 launch mqtt_message_bridge bridge.launch.py \
    config_path:="${MQTT_BRIDGE_CONFIG}" \
    >> "${LOGFILE}" 2>&1 &
BRIDGE_PID=$!
echo $BRIDGE_PID > "${PIDFILE}"
echo "  pid ${BRIDGE_PID}"

# The node exits immediately on a bad config or an unreachable broker, so a
# silent background launch would otherwise look like success.
sleep 3
if ! kill -0 "${BRIDGE_PID}" 2>/dev/null; then
    echo "Error: bridge exited during startup. Last lines of ${LOGFILE}:"
    tail -n 20 "${LOGFILE}"
    rm -f "${PIDFILE}"
    exit 1
fi
echo "✓ MQTT bridge started"
