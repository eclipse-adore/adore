#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/common.sh"

echo "--- Building base Docker image ${DOCKER_BASE_IMAGE_LATEST} (${DOCKER_BASE_IMAGE_TAGGED}) ---"
docker build \
  -f "${DOCKER_BASE_DOCKERFILE}" \
  -t "${DOCKER_BASE_IMAGE_LATEST}" \
  -t "${DOCKER_BASE_IMAGE_TAGGED}" \
  "${WORKSPACE_ROOT}"

echo "--- Building dev Docker image ${DOCKER_DEV_IMAGE_LATEST} (${DOCKER_DEV_IMAGE_TAGGED}) ---"
docker build \
  -f "${DOCKER_DEV_DOCKERFILE}" \
  --build-arg USER_UID="${USER_UID}" \
  --build-arg USER_GID="${USER_GID}" \
  --build-arg USERNAME="${USER_NAME}" \
  -t "${DOCKER_DEV_IMAGE_LATEST}" \
  -t "${DOCKER_DEV_IMAGE_TAGGED}" \
  "${WORKSPACE_ROOT}"
