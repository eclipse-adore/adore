#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/common.sh"

# Ensure CI image exists
if ! docker image inspect "${DOCKER_CI_IMAGE_LATEST}" >/dev/null 2>&1; then
  "${SCRIPT_DIR}/build_ci_image.sh"
fi

echo "--- Building documentation inside CI Docker container ---"

docker run --rm \
  -v "${WORKSPACE_ROOT}:/workspace" \
  -w "/workspace" \
  "${DOCKER_CI_IMAGE_LATEST}" \
  bash -lc '
    set -e
    cd documentation
    make build
  '
