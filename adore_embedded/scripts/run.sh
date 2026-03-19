#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/adore.env"
if docker ps --format "{{.Names}}" | grep -q "^${CONTAINER_NAME}$"; then
    echo "Already running: ${CONTAINER_NAME}"
else
    docker run --detach \
        --name "${CONTAINER_NAME}" \
        --platform "${DOCKER_PLATFORM}" \
        --network host \
        --user "$(id -u):$(id -g)" \
        --env-file "${SCRIPT_DIR}/container.env" \
        -e ROS_DISTRO="${ROS_DISTRO}" \
        -v "${SCRIPT_DIR}/ros2_workspace:/ros2_workspace" \
        "${IMAGE}" \
        sleep infinity
    echo "Started: ${CONTAINER_NAME}"
fi
