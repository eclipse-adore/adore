#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_FILE="${SCRIPT_DIR}/.hardware_monitor.pid"

if [[ ! -f "${PID_FILE}" ]]; then
    echo "No PID file found; hardware_monitor may not be running."
    exit 0
fi

PID=$(cat "${PID_FILE}")

if kill -0 "${PID}" 2>/dev/null; then
    echo "Stopping hardware_monitor (PID ${PID})..."
    kill -SIGINT "${PID}"

    TIMEOUT=10
    ELAPSED=0
    while kill -0 "${PID}" 2>/dev/null && [[ ${ELAPSED} -lt ${TIMEOUT} ]]; do
        sleep 1
        ELAPSED=$((ELAPSED + 1))
    done

    if kill -0 "${PID}" 2>/dev/null; then
        echo "Process did not exit cleanly; sending SIGKILL..."
        kill -SIGKILL "${PID}" 2>/dev/null || true
    fi

    echo "hardware_monitor stopped."
else
    echo "Process ${PID} is not running."
fi

rm -f "${PID_FILE}"
