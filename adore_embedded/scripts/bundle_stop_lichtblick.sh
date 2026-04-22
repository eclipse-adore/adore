#!/usr/bin/env bash
set -euo pipefail

LICHTBLICK_CONTAINER="lichtblick_bundle"

if ! command -v podman &>/dev/null; then
    echo "ERROR: podman not found."
    exit 1
fi

podman stop "${LICHTBLICK_CONTAINER}" 2>/dev/null || true
podman rm -f "${LICHTBLICK_CONTAINER}" 2>/dev/null || true
echo "Stopped: ${LICHTBLICK_CONTAINER}"
