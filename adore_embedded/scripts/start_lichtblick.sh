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
source "${SCRIPT_DIR}/lichtblick.env"

if ! docker image inspect "${LICHTBLICK_IMAGE}" >/dev/null 2>&1; then
    ARCHIVE="${SCRIPT_DIR}/lichtblick/${LICHTBLICK_ARCHIVE_NAME}"
    if [ ! -f "${ARCHIVE}" ]; then
        echo "ERROR: Lichtblick image '${LICHTBLICK_IMAGE}' not found and archive missing: ${ARCHIVE}"
        exit 1
    fi
    echo "Loading lichtblick image from ${ARCHIVE}..."
    docker load -i "${ARCHIVE}"
fi

cd "${SCRIPT_DIR}/lichtblick"
exec make start
