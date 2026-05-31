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

LICHTBLICK_CONTAINER="lichtblick_bundle"

if ! command -v podman &>/dev/null; then
    echo "ERROR: podman not found."
    exit 1
fi

podman stop "${LICHTBLICK_CONTAINER}" 2>/dev/null || true
podman rm -f "${LICHTBLICK_CONTAINER}" 2>/dev/null || true
echo "Stopped: ${LICHTBLICK_CONTAINER}"
