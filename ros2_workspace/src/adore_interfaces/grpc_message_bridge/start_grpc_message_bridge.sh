#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [[ -f "$SCRIPT_DIR/.secrets.env" ]]; then
    set -a
    source "$SCRIPT_DIR/.secrets.env"
    set +a
fi

: "${GRPC_ENDPOINT:?GRPC_ENDPOINT not set, source .secrets.env}"

export PYTHONPATH="${PYTHONPATH:-}:$SCRIPT_DIR/proto/generated"

GRPC_HOST="${GRPC_HOST:-0.0.0.0}"
GRPC_PORT="${GRPC_PORT:-50051}"
BRIDGE_CONFIG_PATH="${BRIDGE_CONFIG_PATH:-$(dirname "$0")/config/bridge_config.yaml}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export PYTHONPATH="$PYTHONPATH:$(pwd)/proto/generated"


# Set USE_LOCAL_GRPC_SERVER=1 to start a local gRPC server before the bridge node.
if [[ "${USE_LOCAL_GRPC_SERVER:-}" == "1" ]]; then
    "$SCRIPT_DIR/start_local_grpc_server.sh"
fi

RMW_IMPLEMENTATION=rmw_fastrtps_cpp ros2 launch grpc_message_bridge bridge.launch.py \
    grpc_host:="$GRPC_HOST" \
    grpc_port:="$GRPC_PORT" \
    config_path:="$BRIDGE_CONFIG_PATH"
