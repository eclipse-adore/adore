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

# Remove ADORe Docker images and the dev container.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=/dev/null
source "${SCRIPT_DIR}/common.sh"

require_host "You appear to be inside a container; image cleanup should be done on the host."

echo "--- Removing dev container '${DOCKER_CONTAINER_NAME}' if it exists ---"
docker rm -f "${DOCKER_CONTAINER_NAME}" >/dev/null 2>&1 || true

echo "--- Removing ADORe Docker images for this workspace (tag: ${IMAGE_TAG}) ---"
# Remove dev + CI images belonging to this workspace.
for repo in "${DOCKER_DEV_IMAGE_BASE}" "${DOCKER_CI_IMAGE_BASE}" "${DOCKER_BASE_IMAGE_BASE}"; do
  # Remove the specific tagged image
  if docker image inspect "${repo}:${IMAGE_TAG}" >/dev/null 2>&1; then
    echo "  -> Removing image '${repo}:${IMAGE_TAG}'"
    docker rmi -f "${repo}:${IMAGE_TAG}" || true
  fi
  # Remove the workspace-specific 'latest' tag
  if docker image inspect "${repo}:latest-${WORKSPACE_HASH}" >/dev/null 2>&1; then
    echo "  -> Removing image '${repo}:latest-${WORKSPACE_HASH}'"
    docker rmi -f "${repo}:latest-${WORKSPACE_HASH}" || true
  fi
done
