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

echo "--- Workspace Hash: '${WORKSPACE_HASH}' ---"
echo "--- Base Container Image: '${DOCKER_BASE_IMAGE_TAGGED}' ---"
echo "--- Dev Container Image:  '${DOCKER_DEV_IMAGE_TAGGED}' ---"
echo "--- CI Container Image:   '${DOCKER_CI_IMAGE_TAGGED}' ---"
echo "--- Default Container Name: '${DOCKER_CONTAINER_NAME}' ---"
echo "--- Portable Sharing Tag: '${DOCKER_PORTABLE_TAG}' ---"
