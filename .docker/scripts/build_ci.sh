#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=/dev/null
source "${SCRIPT_DIR}/common.sh"

cd "${WORKSPACE_ROOT}"

docker build \
  -f "${DOCKER_CI_DOCKERFILE}" \
  --build-arg CI_USERNAME="${USER_NAME}" \
  --build-arg CI_USER_UID="${USER_UID}" \
  --build-arg CI_USER_GID="${USER_GID}" \
  -t "${DOCKER_CI_IMAGE_LATEST}" \
  -t "${DOCKER_CI_IMAGE_TAGGED}" \
  .
