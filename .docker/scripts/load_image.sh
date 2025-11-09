#!/usr/bin/env bash
# Load the dev Docker image from a tarball under ${DOCKER_BUILD_DIR}.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=/dev/null
source "${SCRIPT_DIR}/common.sh"

require_host "Saving/loading images should be done from the host."

IN="${DOCKER_BUILD_DIR}/${DOCKER_TAR_NAME}"

if [[ ! -f "${IN}" ]]; then
  echo "ERROR: Image tarball not found: ${IN}" >&2
  echo "       Run save_image.sh first to create it." >&2
  exit 1
fi

echo "--- Loading dev Docker image from ${IN} ---"
docker load -i "${IN}"
