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

if [ -s "${SCRIPT_DIR}/requirements.ppa" ]; then
    apt-get install -y --no-install-recommends software-properties-common
    while IFS= read -r ppa; do
        add-apt-repository -y "$ppa"
    done < "${SCRIPT_DIR}/requirements.ppa"
    apt-get update
fi

if [ -s "${SCRIPT_DIR}/requirements.system" ]; then
    apt-get update
    envsubst < "${SCRIPT_DIR}/requirements.system" \
        | xargs -r apt-get install -y --no-install-recommends
fi

if [ -s "${SCRIPT_DIR}/requirements.pip3" ]; then
    pip3 install --no-cache-dir --break-system-packages \
        -r "${SCRIPT_DIR}/requirements.pip3"
fi
