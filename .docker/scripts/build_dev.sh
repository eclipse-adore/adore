#!/usr/bin/env bash
# Build the base and dev Docker images for ADORe.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=/dev/null
source "${SCRIPT_DIR}/common.sh"

require_host "Hint: to build *inside* the dev container, run colcon directly instead of this script."

cd "${WORKSPACE_ROOT}"

echo "--- Building base Docker image ${DOCKER_BASE_IMAGE_LATEST} (${DOCKER_BASE_IMAGE_TAGGED}) ---"
docker build \
  -f "${DOCKER_BASE_DOCKERFILE}" \
  -t "${DOCKER_BASE_IMAGE_LATEST}" \
  -t "${DOCKER_BASE_IMAGE_TAGGED}" \
  .

echo "--- Building dev Docker image ${DOCKER_DEV_IMAGE_LATEST} (${DOCKER_DEV_IMAGE_TAGGED}) ---"
docker build \
  -f "${DOCKER_DEV_DOCKERFILE}" \
  --build-arg USER_UID="${USER_UID}" \
  --build-arg USER_GID="${USER_GID}" \
  --build-arg USERNAME="${USER_NAME}" \
  -t "${DOCKER_DEV_IMAGE_LATEST}" \
  -t "${DOCKER_DEV_IMAGE_TAGGED}" \
  .
