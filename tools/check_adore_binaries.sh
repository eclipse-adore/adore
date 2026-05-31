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


set -euo pipefail

# Colors
GREEN="\033[0;32m"
YELLOW="\033[0;33m"
NC="\033[0m" # No Color
CHECKMARK="${GREEN}✔${NC}"
WARNING="${YELLOW}⚠${NC}"

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="${SCRIPT_DIR}/.."

LIBRARIES_DIR="${PROJECT_ROOT}/libraries/build"
ROS2_WS_DIR="${PROJECT_ROOT}/ros2_workspace/build"

LIBRARIES_MARKER="build.success"
ROS2_MARKER="build.success"

check_section() {
    local section_name=$1
    local base_dir=$2
    local marker=$3
    local fix_cmd=$4

    echo "    === ${section_name} ==="
    local abs_path="${base_dir}/${marker}"
    local rel_path=$(realpath --relative-to="${PROJECT_ROOT}" "${base_dir}" 2>/dev/null || echo "${base_dir##${PROJECT_ROOT}/}")/${marker}

    if [ -f "${abs_path}" ]; then
        echo -e "    ${CHECKMARK} Found ${rel_path}"
    else
        echo -e "    ${WARNING} Missing ${rel_path}"
        echo -e "    ${YELLOW}Warning: ${section_name} build incomplete. Run \`${fix_cmd}\` to correct this.${NC}"
    fi
}

# Run checks
check_section "ADORe ROS2 Workspace Build Status" "${ROS2_WS_DIR}" "${ROS2_MARKER}" "make build_ros_workspace"

