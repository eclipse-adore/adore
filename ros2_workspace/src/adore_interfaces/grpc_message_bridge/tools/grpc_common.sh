#!/usr/bin/env bash
# Sourced by other scripts. Reads gRPC settings from an .env file if provided,
# then falls back to environment variables, then to defaults.
#
# Usage: source grpc_common.sh [/path/to/grpc.env]

_env_file="${1:-${GRPC_ENV_FILE:-}}"

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

GRPC_HOST="${GRPC_HOST:-localhost}"
GRPC_PORT="${GRPC_PORT:-50051}"
GRPC_ADDRESS="${GRPC_HOST}:${GRPC_PORT}"
