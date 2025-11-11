#!/usr/bin/env bash
# Run tests inside the ADORe CI Docker image, using Justfile targets.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=/dev/null
source "${SCRIPT_DIR}/common.sh"

cd "${WORKSPACE_ROOT}"

IMAGE="${DOCKER_CI_IMAGE_LATEST}"
CONTAINER_NAME="${DOCKER_CI_IMAGE_BASE}_tests"

# Ensure the CI image exists
if ! docker image inspect "${IMAGE}" >/dev/null 2>&1; then
  echo "--- CI image ${IMAGE} not found; building it first ---"
  "${SCRIPT_DIR}/build_ci.sh"
fi

docker run --rm \
  -u "${USER_UID}:${USER_GID}" \
  -v "${WORKSPACE_ROOT}:/home/${USER_NAME}/adore" \
  -w "/home/${USER_NAME}/adore" \
  -e ROS_DISTRO="${ROS_DISTRO}" \
  "${DOCKER_CI_IMAGE_LATEST}" \
  bash -lc '
    set -e
    echo "--- Running ADORe CI tests via just ---"
    just test_ws
  '

