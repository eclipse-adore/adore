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

# Convenience wrapper: run tests + docs using the CI Docker image.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=/dev/null
source "${SCRIPT_DIR}/common.sh"



# ---------------------------------------------------------------------------
# On arm64, disable the sumo_bridge package via COLCON_IGNORE
# ---------------------------------------------------------------------------
ARCH="$(uname -m)"
COLCON_WS_ROOT="${WORKSPACE_ROOT}"
if [[ "${DOCKER_DEFAULT_PLATFORM:-}" == "linux/arm64" || "${ARCH}" == "aarch64" ]]; then
  SUMO_BRIDGE_DIR="${COLCON_WS_ROOT}/adore_interfaces/sumo_bridge"

  if [[ -d "${SUMO_BRIDGE_DIR}" ]]; then
    echo "Disabling sumo_bridge on arm64 via COLCON_IGNORE"
    touch "${SUMO_BRIDGE_DIR}/COLCON_IGNORE"
  else
    echo "sumo_bridge package directory not found at ${SUMO_BRIDGE_DIR}, skipping COLCON_IGNORE"
  fi
fi

# --------------------------------------------------------------------
# Ensure ci image exists; build it if needed
# --------------------------------------------------------------------
if ! docker image inspect "${DOCKER_CI_IMAGE_LATEST}" >/dev/null 2>&1; then
  echo "--- ci image ${DOCKER_CI_IMAGE_LATEST} not found; building it ---"
  "${SCRIPT_DIR}/build_ci.sh"
fi


# ---------------------------------------------------------------------------
# Run build + tests + docs inside the CI image
# ---------------------------------------------------------------------------

# Default for COLCON_WS_ROOT inside the container (relative to repo root)
CONTAINER_COLCON_WS_ROOT="${CONTAINER_COLCON_WS_ROOT:-.}"

echo "--- Running CI in Docker image ${DOCKER_CI_IMAGE_LATEST} ---"
docker run --rm \
  -v "${WORKSPACE_ROOT}:/home/${USER_NAME}/adore" \
  -w "/home/${USER_NAME}/adore" \
  -e ROS_DISTRO="${ROS_DISTRO}" \
  -e COLCON_WS_ROOT="${CONTAINER_COLCON_WS_ROOT}" \
  -e COLCON_COVERAGE_ARGS="--cmake-args -DCMAKE_BUILD_TYPE=Debug -DCMAKE_CXX_FLAGS=--coverage -DCMAKE_C_FLAGS=--coverage -DCMAKE_POSITION_INDEPENDENT_CODE=ON" \
  "${DOCKER_CI_IMAGE_LATEST}" \
  bash -lc '
  just docs_all
  '

echo "--- CI run finished ---"
