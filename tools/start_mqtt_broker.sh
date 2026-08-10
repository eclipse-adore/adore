#!/usr/bin/env bash
SCRIPT_DIRECTORY="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
SOURCE_DIRECTORY="$(realpath "${SCRIPT_DIRECTORY}/..")"

source "${SOURCE_DIRECTORY}/adore.env" 2>/dev/null || true

# MQTT_BROKER_HOST/PORT are the pre-rename names, still honoured.
BROKER_HOST="${MQTT_HOST:-${MQTT_BROKER_HOST:-127.0.0.1}}"
BROKER_PORT="${MQTT_PORT:-${MQTT_BROKER_PORT:-1883}}"
LOG_DIR="${SOURCE_DIRECTORY}/.log/mqtt"
PIDFILE="${LOG_DIR}/mqtt_broker.pid"
LOGFILE="${LOG_DIR}/mqtt_broker.log"
CONFFILE="${LOG_DIR}/mqtt_broker.conf"

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

# mosquitto 2.x refuses every connection without an explicit listener and
# anonymous grant, so the settings are written out rather than passed as flags.
cat > "${CONFFILE}" <<EOF
listener ${BROKER_PORT} ${BROKER_HOST}
allow_anonymous true
persistence false
EOF

echo "Starting mosquitto -> ${LOGFILE}"
mosquitto -c "${CONFFILE}" >> "${LOGFILE}" 2>&1 &
BROKER_PID=$!

# Own PID rather than pgrep, which would latch onto an unrelated instance.
echo "${BROKER_PID}" > "${PIDFILE}"
echo "  pid ${BROKER_PID}"

for _ in $(seq 25); do
    nc -z -w1 "${BROKER_HOST}" "${BROKER_PORT}" 2>/dev/null && break
    kill -0 "${BROKER_PID}" 2>/dev/null || break
    sleep 0.2
done

if ! nc -z -w3 "${BROKER_HOST}" "${BROKER_PORT}" 2>/dev/null; then
    echo "Error: broker not reachable at ${BROKER_HOST}:${BROKER_PORT}. Check ${LOGFILE}"
    tail -n 20 "${LOGFILE}"
    rm -f "${PIDFILE}"
    exit 1
fi
echo "✓ MQTT broker reachable at ${BROKER_HOST}:${BROKER_PORT}"
