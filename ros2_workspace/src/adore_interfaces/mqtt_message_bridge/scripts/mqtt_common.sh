#!/usr/bin/env bash
# Sourced by other scripts. Resolves connection settings from bridge_config.yaml
# (the single source of truth) and exposes them as the _broker_args array.
# Precedence: real environment > env_file in the config > config defaults.
#
# Usage: source mqtt_common.sh [/path/to/bridge_config.yaml]
# Defaults to <pkg>/bridge_config.yaml.

_COMMON_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
_PKG_ROOT="$(cd "$_COMMON_DIR/.." && pwd)"
export MQTT_BRIDGE_CERT_DIR="${MQTT_BRIDGE_CERT_DIR:-$_PKG_ROOT/certs}"

_config="${1:-$_PKG_ROOT/bridge_config.yaml}"
if [[ ! -f "$_config" ]]; then
    echo "ERROR: bridge config not found: $_config" >&2
    exit 1
fi

mapfile -d '' _broker_args < <(python3 "$_COMMON_DIR/bridge_mqtt_args.py" "$_config")
if [[ ${#_broker_args[@]} -eq 0 ]]; then
    echo "ERROR: failed to parse bridge config: $_config" >&2
    exit 1
fi

MQTT_HOST=""; MQTT_PORT=""; MQTT_USERNAME=""
for ((_i = 0; _i < ${#_broker_args[@]}; _i++)); do
    case "${_broker_args[_i]}" in
        -h) MQTT_HOST="${_broker_args[_i + 1]}" ;;
        -p) MQTT_PORT="${_broker_args[_i + 1]}" ;;
        -u) MQTT_USERNAME="${_broker_args[_i + 1]}" ;;
    esac
done
