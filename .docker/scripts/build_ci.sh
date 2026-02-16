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
# shellcheck source=/dev/null
source "${SCRIPT_DIR}/common.sh"

cd "${WORKSPACE_ROOT}"

# Ensure the base image exists (adore_base:latest)
if ! docker image inspect "${DOCKER_BASE_IMAGE_LATEST}" >/dev/null 2>&1; then
  # Check if we have the portable base image (e.g. from cache or load)
  if docker image inspect "${DOCKER_BASE_IMAGE_BASE}:${DOCKER_PORTABLE_TAG}" >/dev/null 2>&1; then
    echo "--- Found portable base image ${DOCKER_BASE_IMAGE_BASE}:${DOCKER_PORTABLE_TAG} ---"
    echo "--- Retagging as ${DOCKER_BASE_IMAGE_LATEST} to match current workspace hash ---"
    docker tag "${DOCKER_BASE_IMAGE_BASE}:${DOCKER_PORTABLE_TAG}" "${DOCKER_BASE_IMAGE_LATEST}"
    docker tag "${DOCKER_BASE_IMAGE_BASE}:${DOCKER_PORTABLE_TAG}" "${DOCKER_BASE_IMAGE_TAGGED}"
  else
    echo "--- Building base Docker image ${DOCKER_BASE_IMAGE_LATEST} (${DOCKER_BASE_IMAGE_TAGGED}) ---"
    docker build \
      -f "${DOCKER_BASE_DOCKERFILE}" \
      -t "${DOCKER_BASE_IMAGE_LATEST}" \
      -t "${DOCKER_BASE_IMAGE_TAGGED}" \
      .
  fi
fi

echo "--- Building CI Docker image ${DOCKER_CI_IMAGE_LATEST} (${DOCKER_CI_IMAGE_TAGGED}) ---"
docker build \
  -f "${DOCKER_CI_DOCKERFILE}" \
  --build-arg BASE_IMAGE="${DOCKER_BASE_IMAGE_LATEST}" \
  --build-arg USER_UID="${USER_UID}" \
  --build-arg USER_GID="${USER_GID}" \
  --build-arg USERNAME="${USER_NAME}" \
  -t "${DOCKER_CI_IMAGE_LATEST}" \
  -t "${DOCKER_CI_IMAGE_TAGGED}" \
  .
