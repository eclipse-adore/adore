#!/usr/bin/env bash

# Common config for all Docker helper scripts.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Repo root (two levels up from .docker/scripts)
WORKSPACE_ROOT="${WORKSPACE_ROOT:-$(cd "${SCRIPT_DIR}/../.." && pwd)}"

# ROS distro
ROS_DISTRO="${ROS_DISTRO:-jazzy}"

# Container name for dev CLI
DOCKER_CONTAINER_NAME="${DOCKER_CONTAINER_NAME:-adore_dev}"

# Host user info
USER_NAME="${USERNAME:-${USER:-developer}}"
USER_UID="${USER_UID:-$(id -u)}"
USER_GID="${USER_GID:-$(id -g)}"

# Git + arch info (for tagged images)
GIT_HASH="${GIT_HASH:-$(cd "${WORKSPACE_ROOT}" && git rev-parse --short HEAD 2>/dev/null || echo "local")}"
ARCH="${ARCH:-$(uname -m)}"
IMAGE_TAG="${IMAGE_TAG:-${GIT_HASH}-${ARCH}}"

# ---- Base image (shared by dev & CI) ----
DOCKER_BASE_IMAGE_BASE="${DOCKER_BASE_IMAGE_BASE:-adore_base}"
DOCKER_BASE_IMAGE_TAGGED="${DOCKER_BASE_IMAGE_TAGGED:-${DOCKER_BASE_IMAGE_BASE}:${IMAGE_TAG}}"
DOCKER_BASE_IMAGE_LATEST="${DOCKER_BASE_IMAGE_LATEST:-${DOCKER_BASE_IMAGE_BASE}:latest}"
DOCKER_BASE_DOCKERFILE="${DOCKER_BASE_DOCKERFILE:-${WORKSPACE_ROOT}/.docker/base/Dockerfile}"

# ---- Dev image (used by build/cli) ----
DOCKER_DEV_IMAGE_BASE="${DOCKER_DEV_IMAGE_BASE:-adore_dev}"
DOCKER_DEV_IMAGE_TAGGED="${DOCKER_DEV_IMAGE_TAGGED:-${DOCKER_DEV_IMAGE_BASE}:${IMAGE_TAG}}"
DOCKER_DEV_IMAGE_LATEST="${DOCKER_DEV_IMAGE_LATEST:-${DOCKER_DEV_IMAGE_BASE}:latest}"
DOCKER_DEV_DOCKERFILE="${DOCKER_DEV_DOCKERFILE:-${WORKSPACE_ROOT}/.docker/dev/Dockerfile}"

# ---- CI image (used by tests/docs) ----
DOCKER_CI_IMAGE_BASE="${DOCKER_CI_IMAGE_BASE:-adore_ci}"
DOCKER_CI_IMAGE_TAGGED="${DOCKER_CI_IMAGE_TAGGED:-${DOCKER_CI_IMAGE_BASE}:${IMAGE_TAG}}"
DOCKER_CI_IMAGE_LATEST="${DOCKER_CI_IMAGE_LATEST:-${DOCKER_CI_IMAGE_BASE}:latest}"
DOCKER_CI_DOCKERFILE="${DOCKER_CI_DOCKERFILE:-${WORKSPACE_ROOT}/.docker/ci/Dockerfile}"

# Backwards-compat aliases: "dev" is the default image
DOCKER_IMAGE_BASE="${DOCKER_IMAGE_BASE:-${DOCKER_DEV_IMAGE_BASE}}"
DOCKER_IMAGE_TAGGED="${DOCKER_IMAGE_TAGGED:-${DOCKER_DEV_IMAGE_TAGGED}}"
DOCKER_IMAGE_LATEST="${DOCKER_IMAGE_LATEST:-${DOCKER_DEV_IMAGE_LATEST}}"

# Where to store saved images
DOCKER_BUILD_DIR="${DOCKER_BUILD_DIR:-${WORKSPACE_ROOT}/build}"
DOCKER_TAR_NAME="${DOCKER_TAR_NAME:-${DOCKER_DEV_IMAGE_BASE}_${IMAGE_TAG}.tar}"
