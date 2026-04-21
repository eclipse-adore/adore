# ********************************************************************************
# Copyright (c) 2025 Contributors to the Eclipse Foundation
# ********************************************************************************

# Directory where this script lives: .../tools/adore_api
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Repository root two levels up: ../../ from this script
WORKSPACE_ROOT="${WORKSPACE_ROOT:-$(cd "${SCRIPT_DIR}/../.." && pwd)}"

# Workspace root + .log, unless LOG_DIRECTORY is explicitly provided
LOG_DIRECTORY="${LOG_DIRECTORY:-${WORKSPACE_ROOT}/.log}"

# Default API port (can be overridden via env ADORE_API_PORT)
: "${ADORE_API_PORT:=8888}"

start_adore_api() {
    local APP_NAME="adore_api.py"
    local APP_PORT="${ADORE_API_PORT}"
    local LOG_FILE="${LOG_DIRECTORY}/adore_api.log"
    local PID_FILE="${LOG_DIRECTORY}/adore_api.pid"
    local APP_WORKING_DIRECTORY="${WORKSPACE_ROOT}/tools/adore_api"
    
    mkdir -p "${LOG_DIRECTORY}"
    
    if pgrep -f "$APP_NAME" > /dev/null; then
        local old_pid; old_pid=$(pgrep -f "$APP_NAME" | head -1)
        echo "ADORe API is running (PID: $old_pid), access at: http://localhost:$APP_PORT"
        return 0
    fi
    
    if lsof -i :"$APP_PORT" > /dev/null 2>&1; then
        echo "ADORe API port $APP_PORT is already in use"
        return 0
    fi
    
    if [ -f "$PID_FILE" ]; then
        local old_pid
        old_pid=$(cat "$PID_FILE")
        if kill -0 "$old_pid" 2>/dev/null; then
            echo "ADORe API is running (PID: $old_pid), access at: http://localhost:$APP_PORT"
            return 0
        else
            rm -f "$PID_FILE"
        fi
    fi
    
    echo "Starting ADORe API with log directory: ${LOG_DIRECTORY}..."
    local _ros_setup="/opt/ros/${ROS_DISTRO}/setup.bash"
    local _ws_setup="${WORKSPACE_ROOT}/ros2_workspace/install/local_setup.bash"
    local _pyver
    _pyver=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    local _pythonpath="/opt/adore_venv/lib/python${_pyver}/site-packages:/usr/lib/python3/dist-packages:${PYTHONPATH}"
    local _cmd="source '${_ros_setup}' 2>/dev/null"
    _cmd="${_cmd} && { [ -f '${_ws_setup}' ] && source '${_ws_setup}' 2>/dev/null || true; }"
    _cmd="${_cmd} && PYTHONPATH='${_pythonpath}' python3 '${APP_WORKING_DIRECTORY}/$APP_NAME' --log-directory='${LOG_DIRECTORY}'"
    if [ "$(id -u)" = "0" ] && [ -n "${USER:-}" ] && [ "${USER}" != "root" ]; then
        nohup sudo -u "${USER}" bash -c "${_cmd}" > "$LOG_FILE" 2>&1 &
    else
        nohup bash -c "${_cmd}" > "$LOG_FILE" 2>&1 &
    fi
    local app_pid=$!
    
    echo "$app_pid" > "$PID_FILE"
    
    sleep 2
    if kill -0 "$app_pid" 2>/dev/null; then
        echo "ADORe API started successfully (PID: $app_pid), access at: http://localhost:$APP_PORT"
        echo "    Logs: $LOG_FILE"
        echo "    Bag recordings will be stored in: ${LOG_DIRECTORY}/bag_file_recordings/"
    else
        echo "Failed to start ADORe API, review the API log for more info: ${LOG_FILE}"
        rm -f "$PID_FILE"
    fi
}

stop_adore_api() {
    local PID_FILE="${LOG_DIRECTORY}/adore_api.pid"
    
    if [ -f "$PID_FILE" ]; then
        local app_pid
        app_pid=$(cat "$PID_FILE")
        if kill -0 "$app_pid" 2>/dev/null; then
            kill "$app_pid"
            echo "ADORe API stopped (PID: $app_pid)"
        fi
        rm -f "$PID_FILE"
    else
        pkill -f "adore_api.py" 2>/dev/null || true
        echo "ADORe API stopped"
    fi
}

restart_adore_api() {
    stop_adore_api
    sleep 1
    start_adore_api
}

status_adore_api() {
    local APP_NAME="adore_api.py"
    local APP_PORT="${ADORE_API_PORT}"

    if pgrep -f "${APP_NAME}" > /dev/null; then
        echo "ADORe API is running"
        echo "Access at: http://localhost:$APP_PORT"
        echo "Log directory: ${LOG_DIRECTORY}"
        echo "Bag recordings directory: ${LOG_DIRECTORY}/bag_file_recordings/"
        lsof -i :"$APP_PORT" 2>/dev/null | grep LISTEN || true
    else
        echo "ADORe API is not running"
    fi
}


if [ "$(printf '%s' "$ENABLE_ADORE_API" | tr '[:upper:]' '[:lower:]')" != "false" ]; then
    start_adore_api
fi
