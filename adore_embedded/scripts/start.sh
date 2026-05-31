#!/usr/bin/env bash
# ********************************************************************************
# Copyright (c) 2026 Contributors to the Eclipse Foundation
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
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/adore.env"

WORKSPACE="${SCRIPT_DIR}/ros2_workspace"
if [ ! -d "${WORKSPACE}" ]; then
    mkdir -p "${WORKSPACE}"
fi
if [ ! -d "${WORKSPACE}/src" ] && [ -d "${SCRIPT_DIR}/src" ]; then
    cp -r "${SCRIPT_DIR}/src" "${WORKSPACE}/src"
fi
for f in Makefile colcon_defaults.yaml colcon_defaults.yaml.template; do
    if [ -f "${SCRIPT_DIR}/${f}" ] && [ ! -f "${WORKSPACE}/${f}" ]; then
        cp "${SCRIPT_DIR}/${f}" "${WORKSPACE}/${f}"
    fi
done
if [ ! -d "${WORKSPACE}/adore_scenarios" ] && [ -d "${SCRIPT_DIR}/adore_scenarios" ]; then
    cp -r "${SCRIPT_DIR}/adore_scenarios" "${WORKSPACE}/adore_scenarios"
fi

if ! docker image inspect "${IMAGE}" >/dev/null 2>&1; then
    "${SCRIPT_DIR}/load.sh"
fi

if docker ps --format "{{.Names}}" | grep -q "^${CONTAINER_NAME}$"; then
    echo "Already running: ${CONTAINER_NAME}"
else
    docker run --detach \
        --name "${CONTAINER_NAME}" \
        --platform "${DOCKER_PLATFORM}" \
        --network host \
        --user "$(id -u):$(id -g)" \
        --env-file "${SCRIPT_DIR}/container.env" \
        -e ROS_DISTRO="${ROS_DISTRO}" \
        -v "${SCRIPT_DIR}/ros2_workspace:/ros2_workspace" \
        "${IMAGE}" \
        sleep infinity
    echo "Started: ${CONTAINER_NAME}"
fi
