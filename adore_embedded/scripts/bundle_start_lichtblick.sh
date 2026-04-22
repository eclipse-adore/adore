#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/bundle.env"
source "${SCRIPT_DIR}/lichtblick.env"

LICHTBLICK_CONTAINER="lichtblick_bundle"

if ! command -v podman &>/dev/null; then
    echo "ERROR: Lichtblick requires podman. Install podman and re-run."
    exit 1
fi

if podman ps --format "{{.Names}}" | grep -q "^${LICHTBLICK_CONTAINER}$"; then
    echo "Already running: ${LICHTBLICK_CONTAINER}"
    exit 0
fi

if ! podman image exists "${LICHTBLICK_IMAGE}" 2>/dev/null; then
    ARCHIVE="${SCRIPT_DIR}/lichtblick/${LICHTBLICK_ARCHIVE_NAME}"
    if [ ! -f "${ARCHIVE}" ]; then
        echo "ERROR: Lichtblick image '${LICHTBLICK_IMAGE}' not found and archive missing: ${ARCHIVE}"
        exit 1
    fi
    echo "Loading Lichtblick image from ${ARCHIVE}..."
    podman load -i "${ARCHIVE}"
fi

podman run --detach \
    --name "${LICHTBLICK_CONTAINER}" \
    --network host \
    "${LICHTBLICK_IMAGE}"
echo "Started: ${LICHTBLICK_CONTAINER}"
echo ""
echo "Open Lichtblick in a Chromium-based browser:"
echo "  http://localhost:8080/?ds=rosbridge-websocket&ds.url=ws://localhost:9090"
