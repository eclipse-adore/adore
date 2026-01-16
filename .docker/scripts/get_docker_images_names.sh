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

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

source "${SCRIPT_DIR}/common.sh"

echo "--- Base Container Name '${DOCKER_BASE_IMAGE_TAGGED}' ---"
echo "--- Dev Container Name '${DOCKER_DEV_IMAGE_TAGGED}' ---"
echo "--- CI Container Name '${DOCKER_CI_IMAGE_TAGGED}' ---"
