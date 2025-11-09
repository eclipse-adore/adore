#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/common.sh"

# Ensure CI image exists
if ! docker image inspect "${DOCKER_CI_IMAGE_LATEST}" >/dev/null 2>&1; then
  "${SCRIPT_DIR}/build_ci_image.sh"
fi

echo "--- Running tests inside CI Docker container ---"

docker run --rm \
  -v "${WORKSPACE_ROOT}:/workspace" \
  -w "/workspace/.colcon_workspace" \
  -e ROS_DISTRO="${ROS_DISTRO}" \
  "${DOCKER_CI_IMAGE_LATEST}" \
  bash -lc '
    set -e
    echo "Sourcing ROS environment..."
    source "/opt/ros/${ROS_DISTRO}/setup.bash"

    echo "Building with colcon..."
    colcon build --merge-install

    echo "Running tests..."
    colcon test

    echo "Collecting test results..."
    colcon test-result --verbose
  '
