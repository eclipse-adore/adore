#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/adore.env"

bash "${SCRIPT_DIR}/run.sh"
docker exec --workdir /ros2_workspace "${CONTAINER_NAME}" make build
bash "${SCRIPT_DIR}/stop.sh"
