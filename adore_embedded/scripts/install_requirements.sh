#!/usr/bin/env bash
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
