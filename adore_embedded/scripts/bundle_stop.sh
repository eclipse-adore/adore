#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/bundle.env"

if command -v podman &>/dev/null; then
    IMAGE_NAME="adore_bundle_${ROS_DISTRO}"
    if podman image exists "${IMAGE_NAME}" 2>/dev/null; then
        echo "Removing podman image: ${IMAGE_NAME}"
        podman rmi "${IMAGE_NAME}"
        echo "Removed: ${IMAGE_NAME}"
    else
        echo "No podman image found: ${IMAGE_NAME}"
    fi
else
    echo "Bundle uses unshare/chroot — no persistent state to clean up."
fi
