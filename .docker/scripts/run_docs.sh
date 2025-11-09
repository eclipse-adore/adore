#!/usr/bin/env bash
# Build the documentation inside the ADORe CI Docker image.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=/dev/null
source "${SCRIPT_DIR}/common.sh"

require_host "Inside the dev container, you can build docs via: just docs_build"

cd "${WORKSPACE_ROOT}"

IMAGE="${DOCKER_CI_IMAGE_LATEST}"
CONTAINER_NAME="${DOCKER_CI_IMAGE_BASE}_docs"

# Ensure the CI image exists
if ! docker image inspect "${IMAGE}" >/dev/null 2>&1; then
  echo "--- CI image ${IMAGE} not found; building it first ---"
  "${SCRIPT_DIR}/build_ci.sh"
fi

echo "--- Building docs inside CI Docker container (${CONTAINER_NAME}) ---"
docker run \
  --rm \
  -u "${USER_UID}:${USER_GID}" \
  -e "ROS_DISTRO=${ROS_DISTRO}" \
  -v "${WORKSPACE_ROOT}:/home/${USER_NAME}/adore" \
  -w "/home/${USER_NAME}/adore" \
  "${IMAGE}" \
  bash -lc '
    set -e
    echo "--- Building docs via just docs_build ---"
    just docs_build
  '
