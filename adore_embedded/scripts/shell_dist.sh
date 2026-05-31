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
bash "${SCRIPT_DIR}/start.sh"
docker exec -it --user "$(id -u):$(id -g)" \
    --workdir /ros2_workspace_dist/adore_scenarios/simulation_scenarios \
    "${CONTAINER_NAME}" \
    /bin/bash --init-file /ros2_workspace_dist/install/setup.bash
