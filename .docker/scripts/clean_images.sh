#!/usr/bin/env bash
# Remove ADORe Docker images and the dev container.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=/dev/null
source "${SCRIPT_DIR}/common.sh"

require_host "You appear to be inside a container; image cleanup should be done on the host."

echo "--- Removing dev container '${DOCKER_CONTAINER_NAME}' if it exists ---"
docker rm -f "${DOCKER_CONTAINER_NAME}" >/dev/null 2>&1 || true

echo "--- Removing ADORe Docker images (dev, CI, base) ---"
# Remove dev + CI images before base to avoid dependency issues.
for repo in "${DOCKER_DEV_IMAGE_BASE}" "${DOCKER_CI_IMAGE_BASE}" "${DOCKER_BASE_IMAGE_BASE}"; do
  ids=$(docker images --format '{{.Repository}} {{.ID}}' | awk -v repo="$repo" '$1 == repo {print $2}')
  if [[ -n "${ids}" ]]; then
    echo "  -> Removing images for repository '${repo}'"
    docker rmi -f ${ids} || true
  fi
done
