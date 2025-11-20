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

# Kill lingering ROS 2 / colcon processes.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=/dev/null
source "${SCRIPT_DIR}/common.sh"
source "${SCRIPT_DIR}/env.sh"

# Dev container name can be overridden from env
DOCKER_CONTAINER_NAME="${DOCKER_CONTAINER_NAME:-adore}"

# Repo root: two levels up from .docker/scripts, unless WORKSPACE_ROOT already set
if [[ -n "${WORKSPACE_ROOT-}" ]]; then
  REPO_ROOT="${WORKSPACE_ROOT}"
else
  REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
fi

echo "=== Forcefully killing lingering ROS 2 / colcon processes ==="

if is_in_docker; then
  # --------------------------------------------------------------
  # Running *inside* a container (dev or CI)
  # --------------------------------------------------------------
  echo "[container] Cleaning ROS 2 / colcon processes inside this container..."

  echo "-> Killing ros2/colcon wrapper processes..."
  pkill -f "ros2 launch"       || true
  pkill -f "ros2 run"          || true
  pkill -f "python3.*launch"   || true
  pkill -f "rclpy"             || true
  pkill -f "ros2 daemon"       || true
  pkill -f "colcon"            || true

  echo "-> Killing workspace binaries from build tree (container)..."
  # Prefer REPO_ROOT if set; fall back to $HOME/adore
  workspace_root_in_container="${REPO_ROOT:-$HOME/adore}"
  workspace_pattern="${workspace_root_in_container}/.colcon_workspace/build"
  pids=$(ps axo pid,command | grep "$workspace_pattern" | grep -v grep | awk '{print $1}')
  if [ -n "$pids" ]; then
    echo "   Killing workspace processes: $pids"
    kill -9 $pids || true
  else
    echo "   No workspace binary processes found."
  fi

else
  # --------------------------------------------------------------
  # Running on the host
  # --------------------------------------------------------------
  echo "[host] Cleaning host + dev container (if running)"
  echo "Workspace root: ${REPO_ROOT}"
  echo "Dev container : ${DOCKER_CONTAINER_NAME}"

  # 1) Inside dev container
  if docker ps --format '{{.Names}}' | grep -qx "${DOCKER_CONTAINER_NAME}"; then
    echo "-> Killing ROS 2 processes inside dev container '${DOCKER_CONTAINER_NAME}'..."
    docker exec "${DOCKER_CONTAINER_NAME}" bash -lc '
      set -e
      echo "   (container) Killing ros2/colcon wrappers..."
      pkill -f "ros2 launch"       || true
      pkill -f "ros2 run"          || true
      pkill -f "python3.*launch"   || true
      pkill -f "rclpy"             || true
      pkill -f "ros2 daemon"       || true
      pkill -f "colcon"            || true

      echo "   (container) Killing workspace binaries from build tree..."
      workspace_pattern="$HOME/adore/.colcon_workspace/build"
      pids=$(ps axo pid,command | grep "$workspace_pattern" | grep -v grep | awk "{print \$1}")
      if [ -n "$pids" ]; then
        echo "      PIDs: $pids"
        kill -9 $pids || true
      else
        echo "      No workspace binary processes found."
      fi
    '
  else
    echo "-> Dev container '${DOCKER_CONTAINER_NAME}' not running; skipping container cleanup."
  fi

fi

echo "=== Done. ==="
