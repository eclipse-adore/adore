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

# Prepare .colcon_workspace/src (symlinks into src/ etc.)
"${SCRIPT_DIR}/setup_colcon_src.sh"

# ---------------------------------------------------------------------------
# On arm64, disable the sumo_bridge package via COLCON_IGNORE
# ---------------------------------------------------------------------------
ARCH="$(uname -m)"
COLCON_WS_ROOT="${WORKSPACE_ROOT}/.colcon_workspace"
if [[ "${DOCKER_DEFAULT_PLATFORM:-}" == "linux/arm64" || "${ARCH}" == "aarch64" ]]; then
  SUMO_BRIDGE_DIR="${COLCON_WS_ROOT}/src/adore_interfaces/sumo_bridge"

  if [[ -d "${SUMO_BRIDGE_DIR}" ]]; then
    echo "Disabling sumo_bridge on arm64 via COLCON_IGNORE"
    touch "${SUMO_BRIDGE_DIR}/COLCON_IGNORE"
  else
    echo "sumo_bridge package directory not found at ${SUMO_BRIDGE_DIR}, skipping COLCON_IGNORE"
  fi
fi

# ---------------------------------------------------------------------------
# Run build + tests + docs inside the CI image
# ---------------------------------------------------------------------------

# Default for COLCON_WS_ROOT inside the container (relative to repo root)
CONTAINER_COLCON_WS_ROOT="${CONTAINER_COLCON_WS_ROOT:-.colcon_workspace}"

echo "--- Running CI in Docker image ${DOCKER_CI_IMAGE_LATEST} ---"
docker run --rm -it \
  -v "${WORKSPACE_ROOT}:/home/${USER_NAME}/adore" \
  -w "/home/${USER_NAME}/adore" \
  -e ROS_DISTRO="${ROS_DISTRO}" \
  -e COLCON_WS_ROOT="${CONTAINER_COLCON_WS_ROOT}" \
  -e COLCON_COVERAGE_ARGS="--cmake-args -DCMAKE_BUILD_TYPE=Debug -DCMAKE_CXX_FLAGS=--coverage -DCMAKE_C_FLAGS=--coverage -DCMAKE_POSITION_INDEPENDENT_CODE=ON" \
  "${DOCKER_CI_IMAGE_LATEST}" \
  bash -lc '
    set -euo pipefail
    echo "--- Inside CI container ---"
    echo "ROS_DISTRO=$ROS_DISTRO"
    echo "COLCON_WS_ROOT=${COLCON_WS_ROOT}"
    echo "PWD=$(pwd)"   # should be /home/${USER_NAME}/adore

    just build
    just test_ws


    if command -v gcovr >/dev/null 2>&1; then
      echo "--- Generating coverage reports with gcovr ---"
      mkdir -p .gcovr_reports
      # XML
      gcovr \
        . \
        -r . \
        --exclude 'vendor/.*' \
        --exclude 'adore_interfaces/.*' \
        --exclude '.*rosidl.*' \
        --xml-pretty \
        --output .gcovr_reports/coverage.xml

      # HTML
      gcovr \
        . \
        -r . \
        --exclude 'vendor/.*' \
        --exclude 'adore_interfaces/.*' \
        --exclude '.*rosidl.*' \
        --html-details \
        --output .gcovr_reports/coverage.html
    else
      echo "gcovr not found in CI image, skipping coverage generation"
    fi

    just docs_build


  '

echo "--- CI run finished ---"
