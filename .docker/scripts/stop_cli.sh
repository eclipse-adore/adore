#!/usr/bin/env bash
# Stop and remove the dev CLI container.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=/dev/null
source "${SCRIPT_DIR}/common.sh"

require_host "Stopping containers should be done from the host."

CONTAINER_NAME="${DOCKER_CONTAINER_NAME}"

echo "--- Stopping container '${CONTAINER_NAME}' (if running) ---"
docker stop "${CONTAINER_NAME}" >/dev/null 2>&1 || true

echo "--- Removing container '${CONTAINER_NAME}' (if present) ---"
docker rm "${CONTAINER_NAME}" >/dev/null 2>&1 || true
