#!/usr/bin/env bash
# Answers, in order, for the broker named by a bridge config:
#
#   1. is the host reachable?
#   2. does TLS work?
#   3. does authentication work?
#
# Each stage prints what it observed, so a failure identifies the layer that
# broke rather than just "connection failed".
#
# Usage: ./scripts/mqtt_test_remote.sh [/path/to/bridge_config.yaml]

set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PKG_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
source "$SCRIPT_DIR/test_common.sh"

CONFIG="${1:-$PKG_ROOT/config/bridge_config.yaml}"

if [[ ! -f "$CONFIG" ]]; then
    echo "ERROR: config not found: $CONFIG" >&2
    exit 1
fi

export MQTT_BRIDGE_CONFIG="$CONFIG"
export MQTT_BRIDGE_CERT_DIR="${MQTT_BRIDGE_CERT_DIR:-$PKG_ROOT/certs}"

WORK_DIR="$(mktemp -d)"
trap 'rm -rf "$WORK_DIR"' EXIT

probe() {
    local stage="$1" name="$2"
    local out status
    out="$(python3 "$SCRIPT_DIR/mqtt_probe.py" --stage "$stage" --config "$CONFIG" 2>&1)"
    status=$?
    echo "  $out"
    if [[ "$status" -eq 2 ]]; then
        skip "$name" "not applicable"
        return 0
    fi
    record "$name" "$status"
    return "$status"
}

echo "=== Remote Broker Test ==="
echo "Config : $CONFIG"

# Resolving the mosquitto arguments first turns missing certificates into a skip
# rather than the hard exit mqtt_common.sh would take.
if ! python3 "$SCRIPT_DIR/bridge_mqtt_args.py" "$CONFIG" > /dev/null 2> "$WORK_DIR/args.err"; then
    echo "SKIP: cannot resolve broker settings from $CONFIG"
    sed 's/^/      /' "$WORK_DIR/args.err"
    exit 0
fi
source "$SCRIPT_DIR/mqtt_common.sh" "$CONFIG"

echo "Broker : $MQTT_HOST:$MQTT_PORT"
echo "User   : ${MQTT_USERNAME:-<anonymous>}"

banner "1. Is the host reachable?"
if ! probe tcp "host reachable ($MQTT_HOST:$MQTT_PORT)"; then
    echo "  nothing below this layer can be tested." >&2
    summary
    exit 1
fi

banner "2. Is TLS working?"
if ! probe tls "tls handshake"; then
    echo "  nothing below this layer can be tested." >&2
    summary
    exit 1
fi

banner "3. Does authentication work?"
if [[ -z "${MQTT_USERNAME:-}" || -z "${MQTT_PASSWORD:-}" ]]; then
    skip "broker authentication" "no credentials in the environment or the env_file"
    summary
    exit 0
fi
if ! probe auth "broker authentication"; then
    summary
    exit 1
fi

summary
