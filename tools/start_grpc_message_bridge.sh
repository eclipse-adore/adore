#!/usr/bin/env bash
SCRIPT_DIRECTORY="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
export SOURCE_DIRECTORY="$(realpath "${SCRIPT_DIRECTORY}/..")"

source "${SOURCE_DIRECTORY}/adore.env"
source "/opt/ros/${ROS_DISTRO}/setup.bash" 2>/dev/null || true

ROS2_WORKSPACE_DIRECTORY="${SOURCE_DIRECTORY}/ros2_workspace"
if [ -f "${ROS2_WORKSPACE_DIRECTORY}/install/local_setup.bash" ]; then
    source "${ROS2_WORKSPACE_DIRECTORY}/install/local_setup.bash"
fi

LOG_DIR="${SOURCE_DIRECTORY}/.log/grpc"
PIDFILE="${LOG_DIR}/grpc_bridge.pid"
LOGFILE="${LOG_DIR}/grpc_bridge.log"

mkdir -p "${LOG_DIR}"

if [ "${GRPC_BRIDGE_ENABLE:-false}" != "true" ]; then
    exit 0
fi

if [ -f "${PIDFILE}" ] && kill -0 "$(cat "${PIDFILE}")" 2>/dev/null; then
    echo "✓ gRPC bridge already running (pid $(cat "${PIDFILE}"))"
    exit 0
fi

# OAuth client_id/client_secret are kept out of adore.env and sourced here.
if [ -f "${GRPC_BRIDGE_SECRETS:-}" ]; then
    set -a
    source "${GRPC_BRIDGE_SECRETS}"
    set +a
fi

# proto_registry imports the generated stubs at module load, so the generated
# tree produced by the package build must be importable.
if [ -n "${GRPC_BRIDGE_PROTO_PATH:-}" ]; then
    export PYTHONPATH="${GRPC_BRIDGE_PROTO_PATH}:${PYTHONPATH}"
fi

if [ -z "${GRPC_ENDPOINT:-}" ]; then
    echo "WARNING: GRPC_ENDPOINT is unset; the bridge has no remote to dial" >&2
fi

export RMW_IMPLEMENTATION="${RMW_IMPLEMENTATION:-rmw_fastrtps_cpp}"

echo "Starting grpc_message_bridge -> ${LOGFILE}"
ros2 launch grpc_message_bridge bridge.launch.py \
    config_path:="${GRPC_BRIDGE_CONFIG}" \
    grpc_host:="${GRPC_BRIDGE_HOST:-0.0.0.0}" \
    grpc_port:="${GRPC_BRIDGE_PORT:-50051}" \
    >> "${LOGFILE}" 2>&1 &
BRIDGE_PID=$!
echo $BRIDGE_PID > "${PIDFILE}"
echo "  pid ${BRIDGE_PID}"
