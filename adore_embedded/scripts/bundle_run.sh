#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/bundle.env"

_run_podman() {
    if ! podman image exists adore_bundle_${ROS_DISTRO} 2>/dev/null; then
        echo "Importing rootfs into podman (first run only)..."
        tar -c -C "${SCRIPT_DIR}/rootfs" . \
            | podman import \
                --change "ENV ROS_DISTRO=${ROS_DISTRO}" \
                --change "WORKDIR /ros2_workspace_dist" \
                - "adore_bundle_${ROS_DISTRO}"
    fi
    exec podman run --rm -it \
        --network host \
        --env-file "${SCRIPT_DIR}/container.env" \
        -e ROS_DISTRO="${ROS_DISTRO}" \
        -v "${SCRIPT_DIR}/ros2_workspace_dist:/ros2_workspace_dist:z" \
        "adore_bundle_${ROS_DISTRO}" \
        "$@"
}

_run_unshare() {
    for tool in unshare chroot mount; do
        command -v "$tool" &>/dev/null || {
            echo "ERROR: '${tool}' not found — install util-linux"
            exit 1
        }
    done
    set -a; source "${SCRIPT_DIR}/container.env"; set +a
    exec unshare --user --map-root-user --mount --pid --fork \
        "${SCRIPT_DIR}/.bundle_inner.sh" \
        "${SCRIPT_DIR}/rootfs" \
        "${ROS_DISTRO}" \
        "${SCRIPT_DIR}/ros2_workspace_dist" \
        "$@"
}

if command -v podman &>/dev/null; then
    _run_podman "$@"
else
    _run_unshare "$@"
fi
