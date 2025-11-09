#!/usr/bin/env bash
# Open an interactive dev shell inside the ADORe dev Docker container.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=/dev/null
source "${SCRIPT_DIR}/common.sh"

require_host "You are already inside a container. Use this shell instead of running the dev CLI wrapper again."

WORKSPACE_ROOT="${WORKSPACE_ROOT}"
IMAGE="${DOCKER_DEV_IMAGE_LATEST}"
CONTAINER_NAME="${DOCKER_CONTAINER_NAME}"
USERNAME="${USER_NAME}"

# Ensure the dev image exists
if ! docker image inspect "${IMAGE}" >/dev/null 2>&1; then
  echo "--- Dev image ${IMAGE} not found; building it first ---"
  "${SCRIPT_DIR}/build_dev.sh"
fi

# Attach to a running container if present
if docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}\$"; then
  echo "--- Attaching to running container '${CONTAINER_NAME}' ---"
  exec docker exec -it \
    -e TERM="${TERM:-xterm-256color}" \
    -e COLORTERM="${COLORTERM:-}" \
    "${CONTAINER_NAME}" /usr/bin/zsh -l
fi

# Start an existing stopped container if present
if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}\$"; then
  echo "--- Starting stopped container '${CONTAINER_NAME}' ---"
  docker start "${CONTAINER_NAME}" >/dev/null
  exec docker exec -it \
    -e TERM="${TERM:-xterm-256color}" \
    -e COLORTERM="${COLORTERM:-}" \
    "${CONTAINER_NAME}" /usr/bin/zsh -l
fi

# Otherwise, create a new container
echo "--- Allowing X server access for user '${USERNAME}' ---"
xhost +SI:localuser:"${USERNAME}" >/dev/null 2>&1 || true

set +e
docker run \
  -it \
  --name "${CONTAINER_NAME}" \
  -p 8765:8765 \
  -e DISPLAY="${DISPLAY:-:0}" \
  -e QT_X11_NO_MITSHM=1 \
  -v /tmp/.X11-unix:/tmp/.X11-unix \
  -v "${WORKSPACE_ROOT}:/home/${USERNAME}/adore" \
  --device /dev/dri \
  "${IMAGE}" /usr/bin/zsh -l
RET=$?
set -e

echo "--- Revoking X server access ---"
xhost -SI:localuser:"${USERNAME}" >/dev/null 2>&1 || true

exit "${RET}"
