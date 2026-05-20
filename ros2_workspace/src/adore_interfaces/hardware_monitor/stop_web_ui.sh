#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_FILE="${SCRIPT_DIR}/.hardware_monitor_webui.pid"

if [[ ! -f "${PID_FILE}" ]]; then
    echo "No PID file found; Hardware Monitor UI may not be running."
    exit 0
fi

PID=$(cat "${PID_FILE}")
if kill -0 "${PID}" 2>/dev/null; then
    echo "Stopping Hardware Monitor UI (PID ${PID})..."
    kill -SIGINT "${PID}"
    ELAPSED=0
    while kill -0 "${PID}" 2>/dev/null && [[ ${ELAPSED} -lt 10 ]]; do
        sleep 1; ELAPSED=$((ELAPSED + 1))
    done
    kill -0 "${PID}" 2>/dev/null && kill -SIGKILL "${PID}" 2>/dev/null || true
    echo "Hardware Monitor UI stopped."
else
    echo "Process ${PID} is not running."
fi
rm -f "${PID_FILE}"
