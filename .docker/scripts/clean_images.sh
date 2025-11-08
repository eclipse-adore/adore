#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/common.sh"

echo "--- Removing dev container '${DOCKER_CONTAINER_NAME}' if it exists ---"
if docker ps -a -q -f name=^"${DOCKER_CONTAINER_NAME}"$ >/dev/null 2>&1; then
  docker rm -f "${DOCKER_CONTAINER_NAME}" >/dev/null 2>&1 || true
fi

echo "--- Removing Docker images (dev, CI, base) if they exist ---"

for img in \
  "${DOCKER_DEV_IMAGE_LATEST}" "${DOCKER_DEV_IMAGE_TAGGED}" \
  "${DOCKER_CI_IMAGE_LATEST}" "${DOCKER_CI_IMAGE_TAGGED}" \
  "${DOCKER_BASE_IMAGE_LATEST}" "${DOCKER_BASE_IMAGE_TAGGED}"
do
  if [[ -n "${img}" ]]; then
    docker rmi "${img}" >/dev/null 2>&1 || true
  fi
done
