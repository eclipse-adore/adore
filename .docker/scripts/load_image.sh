#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/common.sh"

IN="${DOCKER_BUILD_DIR}/${DOCKER_TAR_NAME}"

echo "--- Loading dev Docker image from ${IN} ---"
docker load < "${IN}"
echo "Docker image loaded from ${IN}"
