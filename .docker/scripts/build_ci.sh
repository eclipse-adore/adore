#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=/dev/null
source "${SCRIPT_DIR}/common.sh"

cd "${WORKSPACE_ROOT}"

# Ensure the base image exists (adore_base:latest)
if ! docker image inspect "${DOCKER_BASE_IMAGE_LATEST}" >/dev/null 2>&1; then
  echo "--- Building base Docker image ${DOCKER_BASE_IMAGE_LATEST} (${DOCKER_BASE_IMAGE_TAGGED}) ---"
  docker build \
    -f "${DOCKER_BASE_DOCKERFILE}" \
    -t "${DOCKER_BASE_IMAGE_LATEST}" \
    -t "${DOCKER_BASE_IMAGE_TAGGED}" \
    .
fi

echo "--- Building CI Docker image ${DOCKER_CI_IMAGE_LATEST} (${DOCKER_CI_IMAGE_TAGGED}) ---"
docker build \
  -f "${DOCKER_CI_DOCKERFILE}" \
  --build-arg CI_USERNAME="${USER_NAME}" \
  --build-arg CI_USER_UID="${USER_UID}" \
  --build-arg CI_USER_GID="${USER_GID}" \
  -t "${DOCKER_CI_IMAGE_LATEST}" \
  -t "${DOCKER_CI_IMAGE_TAGGED}" \
  .
