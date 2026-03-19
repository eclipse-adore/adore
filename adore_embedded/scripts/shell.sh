#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/adore.env"
bash "${SCRIPT_DIR}/run.sh"
docker exec -it --user "$(id -u):$(id -g)" --workdir /ros2_workspace "${CONTAINER_NAME}" /bin/bash
