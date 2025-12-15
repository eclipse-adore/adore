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

# Load the dev Docker image from a tarball under ${DOCKER_BUILD_DIR}.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=/dev/null
source "${SCRIPT_DIR}/common.sh"

require_host "Saving/loading images should be done from the host."

IN="${DOCKER_BUILD_DIR}/${DOCKER_TAR_NAME}"

if [[ ! -f "${IN}" ]]; then
  echo "ERROR: Image tarball not found: ${IN}" >&2
  echo "       Run save_image.sh first to create it." >&2
  exit 1
fi

echo "--- Loading dev Docker image from ${IN} ---"
docker load -i "${IN}"
