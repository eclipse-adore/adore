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

if find "${SCRIPT_DIR}/vendor" -name '*.deb' | grep -q .; then
    find "${SCRIPT_DIR}/vendor" -name '*.deb' | sort | xargs dpkg -i || true
    apt-get install -f -y --no-install-recommends
else
    echo "No .deb packages found in ${SCRIPT_DIR}/vendor"
fi
