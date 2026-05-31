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

    # Source ROS environment so rclpy is available when running via `make run`
    local ros_distro="${ROS_DISTRO:-humble}"
    local ros_setup="/opt/ros/${ros_distro}/setup.bash"
    if [ -f "$ros_setup" ] && [ -z "${AMENT_PREFIX_PATH:-}" ]; then
        set +u
        source "$ros_setup" 2>/dev/null || true
        set -u
    fi
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
    whoami > adore_api_log.log
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
    nohup bash -c "python3 '${APP_WORKING_DIRECTORY}/${APP_NAME}' \
        --log-directory='${LOG_DIRECTORY}' \
        --workspace-root='${WORKSPACE_ROOT}' \
        --port='${APP_PORT}'" > "$LOG_FILE" 2>&1 &
    local app_pid=$!
    
    echo "$app_pid" > "$PID_FILE"
    
    sleep 2
    if kill -0 "$app_pid" 2>/dev/null; then
        echo "ADORe API started successfully (PID: $app_pid), access at: http://localhost:$APP_PORT"
        echo "    Logs: $LOG_FILE"
        echo "    Bag recordings directory: ${LOG_DIRECTORY}/bag_file_recordings/"
        echo "    Model checking log directory: ${LOG_DIRECTORY}/model_checker/"
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
        echo "Model checking log directory: ${LOG_DIRECTORY}/model_checker/"
        lsof -i :"$APP_PORT" 2>/dev/null | grep LISTEN || true
        echo ""
        workspace_status_adore_api
    else
        echo "ADORe API is not running"
    fi
}

workspace_status_adore_api() {
    local APP_PORT="${ADORE_API_PORT}"
    local BUILD_DIR="${WORKSPACE_ROOT}/ros2_workspace/build"

    echo "--- Workspace ---"
    if command -v curl > /dev/null 2>&1; then
        curl -sf "http://localhost:${APP_PORT}/api/workspace/status" 2>/dev/null \
            | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    print('  ready          :', d.get('ready'))
    print('  build_dir      :', d.get('build_dir'))
    print('  build_exists   :', d.get('build_dir_exists'))
    print('  install_exists :', d.get('install_dir_exists'))
    print('  setup_exists   :', d.get('setup_script_exists'))
    ts = d.get('last_sourced_at')
    if ts:
        import datetime
        print('  last_sourced   :', datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S'))
    if 'error' in d:
        print('  error          :', d['error'])
except Exception as e:
    print('  (could not parse workspace status:', e, ')')
" 2>/dev/null || echo "  (API not reachable on port $APP_PORT)"
    else
        if [ -d "${BUILD_DIR}" ] && [ -n "$(ls -A "${BUILD_DIR}" 2>/dev/null)" ]; then
            echo "  build directory: present (${BUILD_DIR})"
        else
            echo "  build directory: EMPTY or missing -- run colcon build inside ros2_workspace"
        fi
    fi
}


if [ "$(printf '%s' "$ENABLE_ADORE_API" | tr '[:upper:]' '[:lower:]')" != "false" ]; then
    start_adore_api
fi
