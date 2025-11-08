#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/common.sh"

echo "--- Ensuring dev Docker image ${DOCKER_DEV_IMAGE_LATEST} is built ---"
if ! docker image inspect "${DOCKER_DEV_IMAGE_LATEST}" >/dev/null 2>&1; then
  "${SCRIPT_DIR}/build_image.sh"
fi

NAME="${DOCKER_CONTAINER_NAME}"
IMAGE="${DOCKER_DEV_IMAGE_LATEST}"

# Running container: exec into it
if [[ -n "$(docker ps -q -f name=^${NAME}$)" ]]; then
  echo "→ Container '${NAME}' is running; opening a new shell"
  exec docker exec -it \
    --env TERM="${TERM:-xterm-256color}" \
    --env COLORTERM="${COLORTERM:-}" \
    "${NAME}" /usr/bin/zsh -l
fi

# Stopped container: start then exec
if [[ -n "$(docker ps -aq -f status=exited -f name=^${NAME}$)" ]]; then
  echo "→ Container '${NAME}' exists but is stopped; starting…"
  docker start "${NAME}" >/dev/null
  exec docker exec -it \
    --env TERM="${TERM:-xterm-256color}" \
    --env COLORTERM="${COLORTERM:-}" \
    "${NAME}" /usr/bin/zsh -l
fi

# No container yet: create a new one with X11
echo "--- Allowing local Docker container to access X server ---"
xhost +SI:localuser:"${USER_NAME}" >/dev/null 2>&1 || true

echo "→ No container named '${NAME}'; creating a new one"
set -x
docker run -it \
  --name "${NAME}" \
  -p 8765:8765 \
  -e DISPLAY="${DISPLAY:-:0}" \
  -e QT_X11_NO_MITSHM=1 \
  -v /tmp/.X11-unix:/tmp/.X11-unix \
  -v "${WORKSPACE_ROOT}:/home/${USER_NAME}/adore" \
  --device /dev/dri \
  "${IMAGE}" /usr/bin/zsh -l
RET=$?
set +x

echo "--- Revoking X server access ---"
xhost -SI:localuser:"${USER_NAME}" >/dev/null 2>&1 || true

exit "${RET}"
