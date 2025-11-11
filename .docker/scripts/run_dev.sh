#!/usr/bin/env bash
# Run or attach to the ADORe dev container, with persistent zsh history.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=/dev/null
source "${SCRIPT_DIR}/common.sh"

require_host "Use this script from the host, not from inside a container."

cd "${WORKSPACE_ROOT}"

IMAGE="${DOCKER_DEV_IMAGE_LATEST}"
CONTAINER_NAME="${DOCKER_CONTAINER_NAME}"

# --------------------------------------------------------------------
# Ensure dev image exists; build it if needed
# --------------------------------------------------------------------
if ! docker image inspect "${IMAGE}" >/dev/null 2>&1; then
  echo "--- Dev image ${IMAGE} not found; building it ---"
  "${SCRIPT_DIR}/build_dev.sh"
fi

# --------------------------------------------------------------------
# If a container with this name is already running, exec into it
# --------------------------------------------------------------------
if docker ps --format '{{.Names}}' | grep -qx "${CONTAINER_NAME}"; then
  echo "--- Attaching to running dev container ${CONTAINER_NAME} ---"
  clear 
  dev_greeting
  docker exec -it \
    -w "/home/${USER_NAME}/adore/" \
    -e HISTFILE="/home/${USER_NAME}/.zsh_history" \
    -e HISTSIZE=100000 \
    -e SAVEHIST=100000 \
    "${CONTAINER_NAME}" \
    zsh
  exit 0
fi

# If a container with this name exists but is stopped, remove it
if docker ps -a --format '{{.Names}}' | grep -qx "${CONTAINER_NAME}"; then
  echo "--- Removing stopped container ${CONTAINER_NAME} ---"
  docker rm "${CONTAINER_NAME}" >/dev/null
fi

# --------------------------------------------------------------------
# Start a fresh dev container with persistent zsh history
# --------------------------------------------------------------------
HOST_ZSH_HISTORY="${WORKSPACE_ROOT}/.zsh_history"
if [ ! -f "${HOST_ZSH_HISTORY}" ]; then
  touch "${HOST_ZSH_HISTORY}"
fi

echo "--- Starting dev container ${CONTAINER_NAME} (image: ${IMAGE}) ---"
clear
dev_greeting

docker run --rm -it \
  --name "${CONTAINER_NAME}" \
  --network host \
  -e DISPLAY \
  -e QT_X11_NO_MITSHM=1 \
  -v /tmp/.X11-unix:/tmp/.X11-unix:rw \
  -v "${WORKSPACE_ROOT}:/home/${USER_NAME}/adore" \
  -v "${HOST_ZSH_HISTORY}:/home/${USER_NAME}/.zsh_history" \
  -w "/home/${USER_NAME}/adore/" \
  -e ROS_DISTRO="${ROS_DISTRO}" \
  -e HISTFILE="/home/${USER_NAME}/.zsh_history" \
  -e HISTSIZE=100000 \
  -e SAVEHIST=100000 \
  "${IMAGE}"
