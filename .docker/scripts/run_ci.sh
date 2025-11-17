#!/usr/bin/env bash
# ********************************************************************************
# Copyright (c) 2025 Contributors to the Eclipse Foundation
#
# See the NOTICE file(s) distributed with this work for additional
# information regarding copyright ownership.
#
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# https://www.eclipse.org/legal/epl-2.0
#
# SPDX-License-Identifier: EPL-2.0
# ********************************************************************************

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
