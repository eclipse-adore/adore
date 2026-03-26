#!/usr/bin/env bash
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
