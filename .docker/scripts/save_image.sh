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

# Save the dev Docker image to a tarball under ${DOCKER_BUILD_DIR}.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=/dev/null
source "${SCRIPT_DIR}/common.sh"

require_host "Saving/loading images should be done from the host."

mkdir -p "${DOCKER_BUILD_DIR}"

OUT="${DOCKER_BUILD_DIR}/${DOCKER_TAR_NAME}"
PORTABLE_IMAGE="${DOCKER_DEV_IMAGE_BASE}:${DOCKER_PORTABLE_TAG}"

echo "--- Tagging ${DOCKER_DEV_IMAGE_TAGGED} as ${PORTABLE_IMAGE} ---"
docker tag "${DOCKER_DEV_IMAGE_TAGGED}" "${PORTABLE_IMAGE}"

echo "--- Saving dev Docker image ${PORTABLE_IMAGE} to ${OUT} ---"
docker save -o "${OUT}" "${PORTABLE_IMAGE}"
echo "Docker image saved to ${OUT}"

# Cleanup the portable tag locally to keep things clean
docker rmi "${PORTABLE_IMAGE}" >/dev/null 2>&1 || true
