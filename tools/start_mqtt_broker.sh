#!/usr/bin/env bash
SCRIPT_DIRECTORY="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
SOURCE_DIRECTORY="$(realpath "${SCRIPT_DIRECTORY}/..")"

source "${SOURCE_DIRECTORY}/adore.env" 2>/dev/null || true

BROKER_HOST="${MQTT_BROKER_HOST:-localhost}"
BROKER_PORT="${MQTT_BROKER_PORT:-1883}"
LOG_DIR="${SOURCE_DIRECTORY}/.log/mqtt"
PIDFILE="${LOG_DIR}/mqtt_broker.pid"
LOGFILE="${LOG_DIR}/mqtt_broker.log"

mkdir -p "${LOG_DIR}"

if [ "${MQTT_LOCAL_BROKER_ENABLE:-false}" != "true" ]; then
    exit 0
fi

if [ -f "${PIDFILE}" ] && kill -0 "$(cat "${PIDFILE}")" 2>/dev/null; then
    echo "✓ MQTT broker already running (pid $(cat "${PIDFILE}"))"
    exit 0
fi

if ! command -v mosquitto &>/dev/null; then
    echo "Error: mosquitto not found. Install via requirements.system."
    exit 1
fi

echo "Starting mosquitto -> ${LOGFILE}"
mosquitto -p "${BROKER_PORT}" -d >> "${LOGFILE}" 2>&1
sleep 1

BROKER_PID=$(pgrep -n mosquitto)
if [ -z "${BROKER_PID}" ]; then
    echo "Error: mosquitto failed to start. Check ${LOGFILE}"
    exit 1
fi

echo "${BROKER_PID}" > "${PIDFILE}"
echo "  pid ${BROKER_PID}"

if ! nc -z -w3 "${BROKER_HOST}" "${BROKER_PORT}" 2>/dev/null; then
    echo "Error: broker not reachable at ${BROKER_HOST}:${BROKER_PORT}. Check ${LOGFILE}"
    exit 1
fi
echo "✓ MQTT broker reachable at ${BROKER_HOST}:${BROKER_PORT}"
