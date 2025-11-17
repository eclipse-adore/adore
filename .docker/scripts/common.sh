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

# Shared Docker/CI configuration for ADORe scripts.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Load environment helpers (host vs container, etc.)
# shellcheck source=/dev/null
if [[ -f "${SCRIPT_DIR}/env.sh" ]]; then
  source "${SCRIPT_DIR}/env.sh"
fi

# Repository root (where the git repo lives)
WORKSPACE_ROOT="${WORKSPACE_ROOT:-$(cd "${SCRIPT_DIR}/../.." && pwd)}"

# ROS distro
ROS_DISTRO="${ROS_DISTRO:-jazzy}"

# Host user info (used when building dev image / running containers)
USER_NAME="${USER_NAME:-$(id -un)}"
USER_UID="${USER_UID:-$(id -u)}"
USER_GID="${USER_GID:-$(id -g)}"

# Git / arch info for tagging images
GIT_HASH="${GIT_HASH:-$(cd "${WORKSPACE_ROOT}" && git rev-parse --short HEAD 2>/dev/null || echo dev)}"
ARCH="${ARCH:-$(uname -m)}"
IMAGE_TAG="${IMAGE_TAG:-${GIT_HASH}-${ARCH}}"

# Container name for the dev shell
DOCKER_CONTAINER_NAME="${DOCKER_CONTAINER_NAME:-adore}"

# Base image (ROS + apt deps, no user/tooling)
DOCKER_BASE_IMAGE_BASE="${DOCKER_BASE_IMAGE_BASE:-adore_base}"
DOCKER_BASE_IMAGE_TAGGED="${DOCKER_BASE_IMAGE_BASE}:${IMAGE_TAG}"
DOCKER_BASE_IMAGE_LATEST="${DOCKER_BASE_IMAGE_BASE}:latest"
DOCKER_BASE_DOCKERFILE="${DOCKER_BASE_DOCKERFILE:-${WORKSPACE_ROOT}/.docker/base/Dockerfile}"

# Dev image (what developers use locally)
DOCKER_DEV_IMAGE_BASE="${DOCKER_DEV_IMAGE_BASE:-adore_dev}"
DOCKER_DEV_IMAGE_TAGGED="${DOCKER_DEV_IMAGE_BASE}:${IMAGE_TAG}"
DOCKER_DEV_IMAGE_LATEST="${DOCKER_DEV_IMAGE_BASE}:latest"
DOCKER_DEV_DOCKERFILE="${DOCKER_DEV_DOCKERFILE:-${WORKSPACE_ROOT}/.docker/dev/Dockerfile}"

# CI image (used for tests/docs in GitHub Actions and locally)
DOCKER_CI_IMAGE_BASE="${DOCKER_CI_IMAGE_BASE:-adore_ci}"
DOCKER_CI_IMAGE_TAGGED="${DOCKER_CI_IMAGE_BASE}:${IMAGE_TAG}"
DOCKER_CI_IMAGE_LATEST="${DOCKER_CI_IMAGE_LATEST:-${DOCKER_CI_IMAGE_BASE}:latest}"
DOCKER_CI_DOCKERFILE="${DOCKER_CI_DOCKERFILE:-${WORKSPACE_ROOT}/.docker/ci/Dockerfile}"

# Location for saved images
DOCKER_BUILD_DIR="${DOCKER_BUILD_DIR:-${WORKSPACE_ROOT}/build}"
DOCKER_TAR_NAME="${DOCKER_TAR_NAME:-${DOCKER_DEV_IMAGE_BASE}_${IMAGE_TAG}.tar}"


dev_greeting() {
  local mode="${1:-shell}"

  # Only use colors if stdout is a TTY
  if [ -t 1 ]; then
    local RESET="\033[0m"
    local BOLD="\033[1m"
    local DIM="\033[2m"
    local FG_CYAN="\033[36m"
    local FG_BLUE="\033[34m"
    local FG_YELLOW="\033[33m"
    local FG_MAGENTA="\033[35m"
  else
    local RESET="" BOLD="" DIM="" FG_CYAN="" FG_BLUE="" FG_YELLOW="" FG_MAGENTA=""
  fi

  # Try to get a nice OS description; fall back to uname

  local kernel arch user container workspace
  kernel="$(uname -r 2>/dev/null || echo "?")"
  arch="$(uname -m 2>/dev/null || echo "?")"
  user="${USER_NAME:-$(id -un 2>/dev/null || echo "unknown")}"
  container="${DOCKER_CONTAINER_NAME:-adore}"
  workspace="${WORKSPACE_ROOT:-$(pwd)}"

  # Clear screen (if possible)
  if command -v clear >/dev/null 2>&1; then
    clear
  else
    printf '\033c'
  fi

  printf "%b" "${FG_MAGENTA}${BOLD}"
  printf "Welcome to the ADORe Development Environment!\n" 
  printf "%b" "${FG_CYAN}${BOLD}"
                                                                                          
  printf "                                                             ......  .......... .                  \n"
  printf "                                         .. --****++*+++--***##################*#---++.            \n"
  printf "                                     . --#*-+-----+++*##-#####***+++++++++++**+**######--          \n"
  printf "                                  --#******+-----::-+##**+*++++++----------------------*##-        \n"
  printf "                              ::**#*+----+***+----*##+----+-------:::--:::::---::::------*##-      \n"
  printf "                          .:.+**+--------+*++--+###+++++----------..:::::::::----------++*###*:    \n"
  printf "               .:..:--++++###*+++**---------+*##*--*####*-----++**+****########################*   \n"
  printf "         ..----*****************################*+::+***#########################**#*#####***++-.  \n"
  printf "     .:-+******++++****##########################*--*###########*******************#######**+++-   \n"
  printf "    -++*+++******################################****###*#*+**************++++++++***+---+++++--:  \n"
  printf "   .---+--++++*#########**#########**++***########******++----++++++-++++++--+++-++-:... ..--+-++. \n"
  printf "   :::--...:--+---++----+**#####+-:.    .:-++++++++++++----------------------------..----: .-+---. \n"
  printf "  ------:::----+-++*++++*#####+-.  .::..   .-++-++--------------------------------:.-----+: :----  \n"
  printf "  :...::---+*###############*+: .:-:*:-+:.  .---------------------------+++++++++- --+++-*- :--.:  \n"
  printf "  :...  .---****###########*+: .:-+:+:--+-.  ----------+++++++++**++++++++++--+--: -+**+-*-:-..    \n"
  printf "  -.       .--++:----+-++**+- .-+--++++--*:  :--+*****+++++++++--+++-----------:.  .-*#+*+.-.      \n"
  printf "  .....      .:-.   ---*++++:..---++***--*-  :--------------------::::...            :---.::       \n"
  printf "     ..:::..:..:------+-+++-. .-+++*+*--**.  .::::::::....               .....::::::::::::..       \n"
  printf "         ........:::::::::::   .--**+#-*+:                    .......            .......           \n"
  printf "                                 --++-+-   ..........                                              \n"
  printf "                       .....    . .::.::--:::..                                                    \n"
  printf "                                                                                 \n\n"
                                                                 
printf "%b" "${FG_YELLOW}"

printf "  Type %bjust --list%b to see available commands,\n"  "${FG_CYAN}" "${FG_YELLOW}"
printf "  or %bhelp%b inside the container for more information.\n\n"  "${FG_CYAN}" "${FG_YELLOW}"

printf "%b" "${RESET}"

  
}