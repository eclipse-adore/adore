#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if find "${SCRIPT_DIR}/vendor" -name '*.deb' | grep -q .; then
    find "${SCRIPT_DIR}/vendor" -name '*.deb' | sort | xargs dpkg -i || true
    apt-get install -f -y --no-install-recommends
else
    echo "No .deb packages found in ${SCRIPT_DIR}/vendor"
fi
