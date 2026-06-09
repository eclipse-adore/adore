#!/usr/bin/env bash
# Sourced by other scripts. Reads broker settings from a .env file if provided,
# then falls back to environment variables, then to defaults.
#
# Usage: source mqtt_common.sh [/path/to/mqtt.env]

_env_file="${1:-${MQTT_ENV_FILE:-}}"

if [[ -n "$_env_file" ]]; then
    if [[ ! -f "$_env_file" ]]; then
        echo "ERROR: env file not found: $_env_file" >&2
        exit 1
    fi
    set -a
    # shellcheck disable=SC1090
    source "$_env_file"
    set +a
fi

MQTT_HOST="${MQTT_HOST:-localhost}"
MQTT_PORT="${MQTT_PORT:-1883}"
MQTT_USERNAME="${MQTT_USERNAME:-}"
MQTT_PASSWORD="${MQTT_PASSWORD:-}"
# TLS: set MQTT_TLS=1 to enable. Provide MQTT_CA_CERT for a custom CA,
# or leave unset to use the system CA store (/etc/ssl/certs).
MQTT_TLS="${MQTT_TLS:-}"
MQTT_CA_CERT="${MQTT_CA_CERT:-}"

_auth_args=()
if [[ -n "$MQTT_USERNAME" ]]; then
    _auth_args+=(-u "$MQTT_USERNAME")
fi
if [[ -n "$MQTT_PASSWORD" ]]; then
    _auth_args+=(-P "$MQTT_PASSWORD")
fi

_tls_args=()
if [[ -n "$MQTT_TLS" ]]; then
    if [[ -n "$MQTT_CA_CERT" ]]; then
        _tls_args+=(--cafile "$MQTT_CA_CERT")
    else
        _tls_args+=(--capath /etc/ssl/certs)
    fi
fi

_broker_args=(-h "$MQTT_HOST" -p "$MQTT_PORT" "${_auth_args[@]}" "${_tls_args[@]}")
