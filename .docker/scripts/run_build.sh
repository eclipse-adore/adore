#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/common.sh"

# Make sure the dev image exists
if ! docker image inspect "${DOCKER_DEV_IMAGE_LATEST}" >/dev/null 2>&1; then
  "${SCRIPT_DIR}/build_image.sh"
fi

echo "--- Running one-shot dev container for build ---"

docker run --rm -it --name "${DOCKER_CONTAINER_NAME}" \
  -v "${WORKSPACE_ROOT}:/home/${USER_NAME}/adore" \
  -w "/home/${USER_NAME}/adore/colcon_workspace" \
  -e ROS_DISTRO="${ROS_DISTRO}" \
  "${DOCKER_DEV_IMAGE_LATEST}"
