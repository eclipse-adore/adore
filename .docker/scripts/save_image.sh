#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/common.sh"

mkdir -p "${DOCKER_BUILD_DIR}"
OUT="${DOCKER_BUILD_DIR}/${DOCKER_TAR_NAME}"

echo "--- Saving dev Docker image ${DOCKER_DEV_IMAGE_TAGGED} to ${OUT} ---"
docker save "${DOCKER_DEV_IMAGE_TAGGED}" > "${OUT}"
echo "Docker image saved to ${OUT}"
