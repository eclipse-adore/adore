#!/usr/bin/env bash
# ********************************************************************************
# Copyright (c) 2025 Contributors to the Eclipse Foundation
#
# See the NOTICE file(s) distributed with this work for additional
# information regarding copyright ownership.
#
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# https://www.eclipse.org/legal/epl-2.0
#
# SPDX-License-Identifier: EPL-2.0
# ********************************************************************************

set -euo pipefail

# Base image for testing (Ubuntu because the setup script assumes Ubuntu + apt)
IMAGE="ubuntu:24.04"

# URL to use when no local setup script is provided
DEFAULT_SETUP_URL="https://raw.githubusercontent.com/eclipse-adore/adore/develop/tools/adore_setup.sh"

LOCAL_SETUP_PATH="${1:-}"   # Optional: path to local setup script

echo "Pulling base image ${IMAGE} if necessary..."
docker pull "${IMAGE}" >/dev/null

# Common docker run args: mount host docker socket so the setup script can build images
DOCKER_CMD=(docker run --rm -v /var/run/docker.sock:/var/run/docker.sock)

if [[ -n "${LOCAL_SETUP_PATH}" ]]; then
    # --- Local script mode ----------------------------------------------------
    if [[ ! -f "${LOCAL_SETUP_PATH}" ]]; then
        echo "ERROR: Provided setup script '${LOCAL_SETUP_PATH}' not found" >&2
        echo "false"
        exit 1
    fi

    # Resolve to absolute path (without relying on realpath)
    SETUP_ABS_PATH="$(
      cd "$(dirname "${LOCAL_SETUP_PATH}")"
      pwd
    )/$(basename "${LOCAL_SETUP_PATH}")"

    echo "INFO: Testing local setup script: ${SETUP_ABS_PATH}"

    # Mount the local script into the container
    DOCKER_CMD+=(-v "${SETUP_ABS_PATH}:/opt/adore_setup.sh:ro")

    # Command executed inside the container
    # - Install tools (including docker.io + sudo)
    # - Ensure group 'docker' exists (needed for newgrp docker in the setup script)
    # - Run the setup script in headless mode
    RUN_CMD='export DEBIAN_FRONTEND=noninteractive; \
             apt-get update && \
             apt-get install -y ca-certificates curl git sudo docker.io && \
             groupadd -f docker && \
             bash /opt/adore_setup.sh --headless'

else
    # --- Remote script mode ---------------------------------------------------
    echo "INFO: No local setup script provided."
    echo "INFO: Will curl '${DEFAULT_SETUP_URL}' inside the container."

    # No extra volume for the script; it will be downloaded inside the container
    RUN_CMD="export DEBIAN_FRONTEND=noninteractive; \
             apt-get update && \
             apt-get install -y ca-certificates curl git sudo docker.io && \
             groupadd -f docker && \
             bash <(curl -sSL ${DEFAULT_SETUP_URL}) --headless"
fi

# Add image + command to docker run invocation
DOCKER_CMD+=("${IMAGE}" bash -lc "${RUN_CMD}")

echo "Running setup script inside container..."
if "${DOCKER_CMD[@]}"; then
    echo "true"
    exit 0
else
    echo "false"
    exit 1
fi
