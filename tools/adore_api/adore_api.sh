# ********************************************************************************
# Copyright (c) 2025 Contributors to the Eclipse Foundation
#
# See the NOTICE file(s) distributed with this work for additional
# information regarding copyright ownership.
#
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# https://www.eclipse.org/legal/epl-2.0
#
# SPDX-License-Identifier: EPL-2.0
# ********************************************************************************

LOG_DIRECTORY="${SOURCE_DIRECTORY}/.log"

start_adore_api() {
    local APP_NAME="adore_api.py"
    local APP_PORT="${ADORE_API_PORT}"
    local LOG_FILE="${LOG_DIRECTORY}/adore_api.log"
    local PID_FILE="${LOG_DIRECTORY}/adore_api.pid"
    local APP_WORKING_DIRECTORY="${SOURCE_DIRECTORY}/tools/adore_api"
    
    mkdir -p "${LOG_DIRECTORY}"
    
    if pgrep -f "$APP_NAME" > /dev/null; then
        local old_pid=$(cat "$PID_FILE" 2>/dev/null || echo "unknown")
        echo "ADORe API is running (PID: $old_pid), access at: http://localhost:$APP_PORT"
        return 0
    fi
    
    if lsof -i :$APP_PORT > /dev/null 2>&1; then
        echo "ADORe API port $APP_PORT is already in use"
        return 0
    fi
    
    if [ -f "$PID_FILE" ]; then
        local old_pid=$(cat "$PID_FILE")
        if kill -0 "$old_pid" 2>/dev/null; then
            echo "ADORe API is running (PID: $old_pid), access at: http://localhost:$APP_PORT"
            return 0
        else
            rm -f "$PID_FILE"
        fi
    fi
    
    echo "Starting ADORe API with log directory: ${LOG_DIRECTORY}..."
    nohup bash -c "cd '${APP_WORKING_DIRECTORY}' && python3 '$APP_NAME' --log-directory='${LOG_DIRECTORY}'" > "$LOG_FILE" 2>&1 &
    local app_pid=$!
    
    echo $app_pid > "$PID_FILE"
    
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
        local app_pid=$(cat "$PID_FILE")
        if kill -0 "$app_pid" 2>/dev/null; then
            kill "$app_pid"
            echo "ADORe API stopped (PID: $app_pid)"
        fi
        rm -f "$PID_FILE"
    else
        pkill -f "adore_api.py"
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
        lsof -i :$APP_PORT 2>/dev/null | grep LISTEN
    else
        echo "ADORe API is not running"
    fi
}

alias start_adore="start_adore_api"
alias stop_adore="stop_adore_api"
alias restart_adore="restart_adore_api"
alias status_adore="status_adore_api"

if [ "$(printf '%s' "$ENABLE_ADORE_API" | tr '[:upper:]' '[:lower:]')" != "false" ]; then
    start_adore_api
fi
