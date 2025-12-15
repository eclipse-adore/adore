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

echo "--- Saving dev Docker image ${DOCKER_DEV_IMAGE_LATEST} to ${OUT} ---"
docker save -o "${OUT}" "${DOCKER_DEV_IMAGE_LATEST}"
echo "Docker image saved to ${OUT}"
