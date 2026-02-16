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

# Build the base and dev Docker images for ADORe.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=/dev/null
source "${SCRIPT_DIR}/common.sh"

require_host "Hint: to build *inside* the dev container, run colcon directly instead of this script."

cd "${WORKSPACE_ROOT}"

if ! docker image inspect "${DOCKER_BASE_IMAGE_LATEST}" >/dev/null 2>&1; then
  echo "--- Building base Docker image ${DOCKER_BASE_IMAGE_LATEST} (${DOCKER_BASE_IMAGE_TAGGED}) ---"
  docker build \
    -f "${DOCKER_BASE_DOCKERFILE}" \
    -t "${DOCKER_BASE_IMAGE_LATEST}" \
    -t "${DOCKER_BASE_IMAGE_TAGGED}" \
    .
fi

echo "--- Building dev Docker image ${DOCKER_DEV_IMAGE_LATEST} (${DOCKER_DEV_IMAGE_TAGGED}) ---"
docker build \
  -f "${DOCKER_DEV_DOCKERFILE}" \
  --build-arg BASE_IMAGE="${DOCKER_BASE_IMAGE_LATEST}" \
  --build-arg USER_UID="${USER_UID}" \
  --build-arg USER_GID="${USER_GID}" \
  --build-arg USERNAME="${USER_NAME}" \
  -t "${DOCKER_DEV_IMAGE_LATEST}" \
  -t "${DOCKER_DEV_IMAGE_TAGGED}" \
  .
