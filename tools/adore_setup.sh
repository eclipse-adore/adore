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

#
# adore_setup.sh
#
# Description:
# This script sets up/configures ADORe by performing the following tasks:
# - Verifies system requirements, such as sufficient free disk space.
# - Installs Docker or updates Docker to the latest version.
# - Checks the Ubuntu version against supported versions.
# - Anonymously clones the ADORe repository to '~/adore'.
# - Builds the ADORe Docker images and prepares the colcon workspace.
#
# Usage:
# Run this script using one of the following commands:
# 1. Directly from the local file:
#    bash adore_setup.sh
#
# 2. Directly from a remote URL:
#    bash <(curl -sSL https://raw.githubusercontent.com/eclipse-adore/adore/develop/tools/adore_setup.sh)
#    or headless/non-interactive
#    bash <(curl -sSL https://raw.githubusercontent.com/eclipse-adore/adore/develop/tools/adore_setup.sh) --headless

set -euo pipefail

trap 'get_help' EXIT

echoerr() { printf "%b" "$*\n" >&2; }
exiterr() { printf "%b\n" "$@" >&2; exit 1; }

SCRIPT_DIRECTORY="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

CLONE_DIR="${HOME}"
SUPPORTED_UBUNTU_VERSIONS="20.04 20.10 22.04 24.04"
REQUIRED_FREESPACE_GB="20"
EXTERNAL_RESOURCES=("https://pypi.org" "http://archive.canonical.com" "https://registry.hub.docker.com")

ADORE_ORGANIZATION="eclipse-adore"
ADORE_SUPPORT_EMAIL_ADDRESS=opensource-ts@dlr.de
ADORE_REPO="https://github.com/${ADORE_ORGANIZATION}/adore.git"
ADORE_HELP_LINK="${ADORE_REPO}/issues"
ADORE_DOCS_LINK="https://${ADORE_ORGANIZATION}.github.io/adore/"

HEADLESS=0
SKIP_PREREQUISITE_CHECKS=0

setup_complete=false

success() {
    printf "\n"
    printf "ADORe was set up successfully!\n"
    printf "  ADORe Directory: %s/adore\n" "${CLONE_DIR}"
    printf "  Recommended next steps:\n"
    printf "    - Change into the repo:    cd \"%s/adore\"\n" "${CLONE_DIR}"
    printf "    - Start a dev shell:       .docker/scripts/cli.sh\n"
    printf "      (or, if 'just' is installed: just cli)\n"
    printf "  Documentation:  %s\n" "${ADORE_DOCS_LINK}"
    printf "  Help / Issues:  %s\n" "${ADORE_HELP_LINK}"
    printf "\n"
}

failure() {
    printf "\n"
    printf "ERROR: ADORe automated setup failed or was incomplete!\n"
    printf "  The recommended next step is to attempt a manual setup.\n"
    printf "    Visit the documentation: %s\n" "${ADORE_DOCS_LINK}"
    printf "    Or open an issue:        %s\n" "${ADORE_HELP_LINK}"
    printf "\n"
}

get_help() {
    local exit_status=$?
    if [[ "${setup_complete}" == "true" && ${exit_status} -eq 0 ]]; then
        success
    elif [[ ${exit_status} -ne 0 ]]; then
        failure
    fi

    printf "\n\n"
    printf "Having trouble? Reach out to the ADORe team, we are here to help!\n"
    printf "  %s\n" "${ADORE_HELP_LINK}"
    printf "  or send us an email at: %s\n" "${ADORE_SUPPORT_EMAIL_ADDRESS}"
    printf "\n\n"
    exit "${exit_status}"
}

usage() {
  cat << EOF
Usage: $(basename "${BASH_SOURCE[0]}") [OPTIONS]

ADORe automated setup.

Available options:

  -h, --help                      Print this help and exit
  -H, --headless                  Run ADORe installation in headless/non-interactive mode
  -s, --skip-prerequisite-checks  Do not run prerequisite checks for storage, OS, etc.
  -v, --verbose                   Print script debug info
EOF
  exit 0
}

parse_params() {
  while :; do
    case "${1-}" in
      -h|--help)
        usage
        ;;
      -s|--skip-prerequisite-checks)
        SKIP_PREREQUISITE_CHECKS=1
        ;;
      -v|--verbose)
        set -x
        ;;
      -H|--headless)
        HEADLESS=1
        ;;
      -?*)
        exiterr "ERROR: Unknown option: $1"
        ;;
      *)
        break
        ;;
    esac
    shift || true
  done

  return 0
}

prompt_yes_no() {
    while true; do
        read -rp "Do you want to proceed? (yes/no): " choice
        case "${choice}" in
            [Yy]|[Yy][Ee][Ss])
                return 0
                ;;
            [Nn]|[Nn][Oo])
                return 1
                ;;
            *)
                echo "Please enter 'yes' or 'no'."
                ;;
        esac
    done
}

banner() {
read -r -d '' coffee_cup << EOF || true

ADORe will be set up on your system. The following system changes will occur:
  - Your OS version will be checked against supported Ubuntu versions: ${SUPPORTED_UBUNTU_VERSIONS// /, }
    Note: The only hard dependencies for ADORe are Docker and Git;
          however, this automated setup script is supported only on Ubuntu.
          For manual setup please refer to the getting started guide:
          ${ADORE_DOCS_LINK}
  - Docker will be installed or updated using a setup script based on
          the official Docker docs: https://docs.docker.com/engine/install/ubuntu/
  - APT dependencies 'git' (and optionally 'just') will be installed
  - ADORe (${ADORE_REPO}) will be cloned to: ${CLONE_DIR}/adore
  - ADORe dev Docker images will be built via .docker/scripts/build_dev.sh
  - You may be prompted for sudo password (root privileges are needed to install Docker and APT dependencies)

ADORe Requirements:
  - ADORe requires a minimum of ~${REQUIRED_FREESPACE_GB}GB of storage.
    The setup requires downloading 10–20 GB of dependencies depending on configuration from the Ubuntu central APT repository (https://ubuntu.com/server/docs/package-management), Docker Hub, and PyPI.
  - Recent version of Docker (this setup script will install or update Docker)
  - This script is designed and tested for Ubuntu versions 20.04–24.04

Initial setup can take some time depending on system and internet connection.

    ( (
     ) )
  ........
  |      |]
  \\      / 
   \`'--'\`
EOF

    printf "%s\n" "$coffee_cup"
    if [[ ${HEADLESS} -eq 0 ]]; then
        if ! prompt_yes_no; then
            exiterr "ADORe setup aborted."
        fi
    else
        echo "INFO: Doing headless/unattended installation."
    fi
}

check_resources() {
    echo "Checking if required internet resources are accessible..."

    for url in "${EXTERNAL_RESOURCES[@]}"; do
        echo "  Fetching: ${url}"
        if curl -fsSL --head "${url}" >/dev/null 2>&1; then
            echo "    ${url} is reachable"
        else
            echoerr "   ERROR: ${url} is unreachable"
            echoerr "     Unable to reach ${url}. Please check your internet connection, firewall, or proxy."
            exit 1
        fi
    done
}


check_os_version() {
    local os_version="unknown"

    if [[ -r /etc/os-release ]]; then
        # VERSION_ID="24.04"
        os_version="$(grep -E '^VERSION_ID=' /etc/os-release | cut -d'"' -f2 || echo "unknown")"
    elif command -v lsb_release >/dev/null 2>&1; then
        # Fallback if /etc/os-release is missing
        os_version="$(lsb_release -sr || echo "unknown")"
    fi

    if [[ "${os_version}" == "unknown" ]]; then
        exiterr "ERROR: could not determine OS version. Supported Ubuntu versions: ${SUPPORTED_UBUNTU_VERSIONS}"
    fi

    # Match whole tokens only
    case " ${SUPPORTED_UBUNTU_VERSIONS} " in
        *" ${os_version} "*)
            return 0
            ;;
        *)
            exiterr "ERROR: unsupported OS version: ${os_version}. Supported versions: ${SUPPORTED_UBUNTU_VERSIONS}"
            ;;
    esac
}


check_freespace() {
    local freespace current_device
    freespace="$(df -BG --output=avail . | tail -n 1 | tr -dc '0-9')"
    current_device="$(df --output=source . | tail -n 1)"
    if [[ -z "${freespace}" ]]; then
        echo "WARNING: Could not determine free space; continuing anyway."
        return 0
    fi

    if (( freespace < REQUIRED_FREESPACE_GB )); then
        exiterr "ERROR: Not enough free space: ${freespace}GB available and ${REQUIRED_FREESPACE_GB}GB required.\nFree up some space on '${current_device}' and try again."
    fi
}

install_dependencies() {
    echo "Checking APT dependencies (git, curl, ca-certificates)..."

    # Ensure we have a package manager we know how to use
    if ! command -v apt-get >/dev/null 2>&1; then
        echo "WARNING: 'apt-get' not found. This setup script is only supported on Ubuntu."
        echo "         Please install 'git', 'curl', and 'ca-certificates' manually and re-run."
        if ! command -v git >/dev/null 2>&1; then
            exiterr "ERROR: 'git' is required but not installed."
        fi
        return 0
    fi

    sudo apt-get update

    if ! command -v git >/dev/null 2>&1; then
        echo "Installing git..."
        sudo apt-get install -y git
    else
        echo "git is already installed."
    fi

    if ! command -v curl >/dev/null 2>&1; then
        echo "Installing curl and ca-certificates..."
        sudo apt-get install -y curl ca-certificates
    else
        echo "curl is already installed."
        # still ensure ca-certificates is present
        sudo apt-get install -y ca-certificates
    fi

    # Optional: try to install just for convenience
    if ! command -v just >/dev/null 2>&1; then
        echo "Attempting to install 'just' via apt (optional)..."
        if sudo apt-get install -y just >/dev/null 2>&1; then
            echo "INFO: Installed 'just' via apt."
        else
            echo "WARNING: 'just' could not be installed automatically. You can install it manually later if desired."
        fi
    fi
}


install_docker() {
    if command -v docker >/dev/null 2>&1; then
        echo "Docker is already installed. Skipping automatic Docker installation."
        return 0
    fi

    echo "Installing Docker using ADORe helper script..."
    bash <(curl -sSL https://raw.githubusercontent.com/eclipse-adore/adore/develop/tools/install_docker.sh)
}

clone_adore() {
    cd "${CLONE_DIR}"

    if [[ ! -d "adore" ]]; then
        echo "Cloning ADORe into ${CLONE_DIR}/adore..."
        git clone "${ADORE_REPO}"
    else
        echo "Directory ${CLONE_DIR}/adore already exists."
        echo "Attempting to update existing clone..."
        cd "adore"
        if [[ -d .git ]]; then
            git fetch --all --tags || true
            # Try to stay on current branch; fallback to develop if present.
            current_branch="$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "")"
            if [[ "${current_branch}" == "HEAD" || -z "${current_branch}" ]]; then
                if git rev-parse --verify develop >/dev/null 2>&1; then
                    git checkout develop || true
                fi
            fi
            git pull --ff-only || true
        else
            echo "WARNING: ${CLONE_DIR}/adore exists but is not a git repository."
        fi
        cd "${CLONE_DIR}"
    fi

    cd "${CLONE_DIR}/adore"

    if [[ -f ".gitmodules" ]]; then
        echo "Initializing/updating git submodules (using HTTPS)..."
        cp .gitmodules .gitmodules.bak
        sed -i "s|git@github.com:|https://github.com/|g" .gitmodules
        git submodule update --init --recursive
        mv .gitmodules.bak .gitmodules
        git submodule sync --recursive
    fi
}

setup_colcon_workspace() {
    cd "${CLONE_DIR}/adore"

    local setup_script=".docker/scripts/setup_colcon_src.sh"

    if [[ -x "${setup_script}" ]]; then
        echo "Setting up .colcon_workspace/src symlinks..."
        "${setup_script}"
    else
        echo "WARNING: ${setup_script} not found or not executable; skipping colcon workspace symlink setup."
    fi
}

build_adore_dev_images() {
    cd "${CLONE_DIR}/adore"

    if [[ ! -x ".docker/scripts/build_dev.sh" ]]; then
        echo "WARNING: .docker/scripts/build_dev.sh not found; skipping dev image build."
        return
    fi

    echo "Building ADORe base and dev Docker images (this may take a while)..."
    # Use newgrp so a freshly-added docker group membership is picked up
    newgrp docker << END
set -e
cd "${CLONE_DIR}/adore"
.docker/scripts/build_dev.sh
END

    setup_complete=true
}

main() {
    parse_params "$@"
    banner

    if [[ ${SKIP_PREREQUISITE_CHECKS} -eq 0 ]]; then
        check_resources
        check_freespace
        check_os_version
    else
        printf "Prerequisite checks skipped...\n"
    fi

    install_dependencies
    clone_adore
    install_docker
    setup_colcon_workspace
    build_adore_dev_images
}

main "$@"
