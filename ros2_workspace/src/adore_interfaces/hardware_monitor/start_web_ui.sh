#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_FILE="${SCRIPT_DIR}/.hardware_monitor_webui.pid"
PORT="${HARDWARE_MONITOR_UI_PORT:-8889}"
HOST="${HARDWARE_MONITOR_UI_HOST:-0.0.0.0}"

if [[ -f "${PID_FILE}" ]]; then
    EXISTING_PID=$(cat "${PID_FILE}")
    if kill -0 "${EXISTING_PID}" 2>/dev/null; then
        echo "Hardware Monitor UI already running (PID ${EXISTING_PID}) on port ${PORT}"
        exit 0
    else
        rm -f "${PID_FILE}"
    fi
fi

ROS_HOME_DEFAULT="${HOME}/.ros"
ROS_LOG_BASE="${ROS_LOG_DIR:-${ROS_HOME:-${ROS_HOME_DEFAULT}}/log}"
mkdir -p "${ROS_LOG_BASE}"
LOG_FILE="${ROS_LOG_BASE}/hardware_monitor_webui_$(date +%Y%m%d_%H%M%S).log"

echo "Starting Hardware Monitor Web UI on http://${HOST}:${PORT}"
python3 "${SCRIPT_DIR}/web_ui/hardware_monitor_web.py" \
    --port "${PORT}" --host "${HOST}" \
    > "${LOG_FILE}" 2>&1 &

LAUNCH_PID=$!
echo "${LAUNCH_PID}" > "${PID_FILE}"
echo "Hardware Monitor UI started (PID ${LAUNCH_PID})"
echo "Log: ${LOG_FILE}"
echo "URL: http://localhost:${PORT}"
