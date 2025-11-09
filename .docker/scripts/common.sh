#!/usr/bin/env bash
# Shared Docker/CI configuration for ADORe scripts.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Load environment helpers (host vs container, etc.)
# shellcheck source=/dev/null
if [[ -f "${SCRIPT_DIR}/env.sh" ]]; then
  source "${SCRIPT_DIR}/env.sh"
fi

# Repository root (where the git repo lives)
WORKSPACE_ROOT="${WORKSPACE_ROOT:-$(cd "${SCRIPT_DIR}/../.." && pwd)}"

# ROS distro
ROS_DISTRO="${ROS_DISTRO:-jazzy}"

# Host user info (used when building dev image / running containers)
USER_NAME="${USER_NAME:-$(id -un)}"
USER_UID="${USER_UID:-$(id -u)}"
USER_GID="${USER_GID:-$(id -g)}"

# Git / arch info for tagging images
GIT_HASH="${GIT_HASH:-$(cd "${WORKSPACE_ROOT}" && git rev-parse --short HEAD 2>/dev/null || echo dev)}"
ARCH="${ARCH:-$(uname -m)}"
IMAGE_TAG="${IMAGE_TAG:-${GIT_HASH}-${ARCH}}"

# Container name for the dev shell
DOCKER_CONTAINER_NAME="${DOCKER_CONTAINER_NAME:-adore}"

# Base image (ROS + apt deps, no user/tooling)
DOCKER_BASE_IMAGE_BASE="${DOCKER_BASE_IMAGE_BASE:-adore_base}"
DOCKER_BASE_IMAGE_TAGGED="${DOCKER_BASE_IMAGE_BASE}:${IMAGE_TAG}"
DOCKER_BASE_IMAGE_LATEST="${DOCKER_BASE_IMAGE_BASE}:latest"
DOCKER_BASE_DOCKERFILE="${DOCKER_BASE_DOCKERFILE:-${WORKSPACE_ROOT}/.docker/base/Dockerfile}"

# Dev image (what developers use locally)
DOCKER_DEV_IMAGE_BASE="${DOCKER_DEV_IMAGE_BASE:-adore_dev}"
DOCKER_DEV_IMAGE_TAGGED="${DOCKER_DEV_IMAGE_BASE}:${IMAGE_TAG}"
DOCKER_DEV_IMAGE_LATEST="${DOCKER_DEV_IMAGE_BASE}:latest"
DOCKER_DEV_DOCKERFILE="${DOCKER_DEV_DOCKERFILE:-${WORKSPACE_ROOT}/.docker/dev/Dockerfile}"

# CI image (used for tests/docs in GitHub Actions and locally)
DOCKER_CI_IMAGE_BASE="${DOCKER_CI_IMAGE_BASE:-adore_ci}"
DOCKER_CI_IMAGE_TAGGED="${DOCKER_CI_IMAGE_BASE}:${IMAGE_TAG}"
DOCKER_CI_IMAGE_LATEST="${DOCKER_CI_IMAGE_LATEST:-${DOCKER_CI_IMAGE_BASE}:latest}"
DOCKER_CI_DOCKERFILE="${DOCKER_CI_DOCKERFILE:-${WORKSPACE_ROOT}/.docker/ci/Dockerfile}"

# Default "current" image (dev) – convenience alias
DOCKER_IMAGE_BASE="${DOCKER_IMAGE_BASE:-${DOCKER_DEV_IMAGE_BASE}}"
DOCKER_IMAGE_TAGGED="${DOCKER_IMAGE_TAGGED:-${DOCKER_DEV_IMAGE_TAGGED}}"
DOCKER_IMAGE_LATEST="${DOCKER_IMAGE_LATEST:-${DOCKER_DEV_IMAGE_LATEST}}"

# Location for saved images
DOCKER_BUILD_DIR="${DOCKER_BUILD_DIR:-${WORKSPACE_ROOT}/build}"
DOCKER_TAR_NAME="${DOCKER_TAR_NAME:-${DOCKER_DEV_IMAGE_BASE}_${IMAGE_TAG}.tar}"
