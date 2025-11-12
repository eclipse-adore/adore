#!/usr/bin/env bash
# Convenience wrapper: run tests + docs locally using the CI Docker image.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=/dev/null
source "${SCRIPT_DIR}/common.sh"

"${SCRIPT_DIR}/setup_colcon_src.sh"
# ---------------------------------------------------------------------------
# On arm64, disable the sumo_bridge package via COLCON_IGNORE
# ---------------------------------------------------------------------------
ARCH="$(uname -m)"
if [[ "${DOCKER_DEFAULT_PLATFORM:-}" == "linux/arm64" || "${ARCH}" == "aarch64" ]]; then
  COLCON_WS_ROOT="${WORKSPACE_ROOT}/.colcon_workspace"
  SUMO_BRIDGE_DIR="${COLCON_WS_ROOT}/src/adore_interfaces/sumo_bridge"

  if [[ -d "${SUMO_BRIDGE_DIR}" ]]; then
    echo "Disabling sumo_bridge on arm64 via COLCON_IGNORE"
    touch "${SUMO_BRIDGE_DIR}/COLCON_IGNORE"
  else
    echo "sumo_bridge package directory not found at ${SUMO_BRIDGE_DIR}, skipping COLCON_IGNORE"
  fi
fi
"${SCRIPT_DIR}/run_tests.sh"
"${SCRIPT_DIR}/run_docs.sh"
