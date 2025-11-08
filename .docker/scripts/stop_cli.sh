#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/common.sh"

if [[ -n "$(docker ps -q -f name=^${DOCKER_CONTAINER_NAME}$)" ]]; then
  echo "→ Stopping container '${DOCKER_CONTAINER_NAME}'"
  docker stop "${DOCKER_CONTAINER_NAME}" >/dev/null
fi

echo "--- Revoking X server access ---"
xhost -SI:localuser:"${USER_NAME}" >/dev/null 2>&1 || true
