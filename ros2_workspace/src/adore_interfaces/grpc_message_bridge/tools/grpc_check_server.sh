#!/usr/bin/env bash
# Checks gRPC server reachability and reports connection status.
#
# Usage: ./grpc_check_server.sh [/path/to/grpc.env]

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/grpc_common.sh" "${1:-}"

echo "=== gRPC Server Check ==="
echo "Host : $GRPC_HOST"
echo "Port : $GRPC_PORT"
echo ""

if ! nc -z -w3 "$GRPC_HOST" "$GRPC_PORT" 2>/dev/null; then
    echo "FAIL: Cannot reach $GRPC_HOST:$GRPC_PORT" >&2
    exit 1
fi
echo "TCP connection: OK"
echo ""

# grpc_health_probe is available if grpcio-health-checking is installed
if command -v grpc_health_probe &>/dev/null; then
    echo "=== gRPC Health Probe ==="
    grpc_health_probe -addr="$GRPC_ADDRESS" && echo "Health: SERVING" || echo "Health: NOT SERVING"
else
    echo "(grpc_health_probe not available -- TCP reachability confirmed above)"
    echo "Install: pip3 install grpcio-health-checking"
fi
