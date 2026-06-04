#!/usr/bin/env bash
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG="${1:-$SCRIPT_DIR/config/weather_service_config.yaml}"

USE_XTERM=false
if command -v python3 &>/dev/null && [ -f "$CONFIG" ]; then
    USE_XTERM=$(python3 -c "
import sys, yaml
try:
    cfg = yaml.safe_load(open('$CONFIG'))
    print(str(cfg.get('visualizer', {}).get('use_xterm', False)).lower())
except Exception:
    print('false')
")
fi

VISUALIZER_CMD="ros2 run weather_service_interface weather_visualizer_node"

if [ "$USE_XTERM" = "true" ]; then
    if command -v xterm &>/dev/null; then
        exec xterm -e "$VISUALIZER_CMD"
    else
        echo "warning: use_xterm is set but xterm is not installed, falling back to current session" >&2
        exec $VISUALIZER_CMD
    fi
else
    exec $VISUALIZER_CMD
fi
