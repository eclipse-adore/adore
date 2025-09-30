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


#!/bin/bash
#
# adore_setup.sh
#
# Description:
# This script sets up/configures ADORe by performing the following tasks:
# - Verifies system requirements, such as sufficient free disk space.
# - Installs Docker or updates Docker to the latest version
# - Checks the Ubuntu version against supported versions.
# - Anonymously clones the ADORe repository to '~/adore'.
# - Builds the ADORe CLI Docker context and builds the user libraries and ROS nodes.
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

#set -euo pipefail
#set -euo

trap 'get_help' EXIT

echoerr() { printf "%b" "$*\n" >&2;}
exiterr (){ printf "$@\n"; exit 1;}

SCRIPT_DIRECTORY="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"


CLONE_DIR="${HOME}"
SUPPORTED_UBUNTU_VERSIONS="20.04 20.10 22.04 24.04"
REQUIRED_FREESPACE_GB="20"
EXTERNAL_RESOURCES=("https://pypi.org" "http://archive.canonical.com" "https://registry.hub.docker.com")

#ADORE_ORGANIZATION="eclipse"
ADORE_ORGANIZATION="eclipse-adore"
ADORE_SUPPORT_EMAIL_ADDRESS=opensource-ts@dlr.de
ADORE_REPO="https://github.com/${ADORE_ORGANIZATION}/adore.git"
#ADORE_REPO="git@github.com:${ADORE_ORGANIZATION}/adore.git"

ADORE_HELP_LINK="${ADORE_REPO}/issues"
ADORE_DOCS_LINK="https://${ADORE_ORGANIZATION}.github.io/adore/"

HEADLESS=0
SKIP_PREREQUISITE_CHECKS=0

setup_complete=false

success(){
    printf "\n"
    printf "ADORe was setup successfully!\n"
    printf "  ADORe Directory: ${CLONE_DIR}/adore \n"
    printf "  Use: 'cd ${CLONE_DIR}/adore && make cli' to get started \n"
    printf "  Read the docs: ${ADORE_DOCS_LINK} \n"
    printf "  Get help: ${ADORE_HELP_LINK}\n"
    printf "\n"
}

failure(){
    printf "\n"
    printf "ERROR: ADORe automated setup failed or was incomplete!\n"
    printf "  The recomended next step is to attempt a manual setup."
    printf "    visit: ${ADORE_HELP_LINK}/mkdocs/getting_started/getting_started/\n"
    printf "\n"
}

get_help(){
    local exit_status=$?
    if [[ "$setup_complete" == "true" && $exit_status -ne 0 ]]; then
        success
    else
        failure
    fi
    printf "\n\n"
    printf "Having trouble? Reach out to the ADORe team, we are here to help!\n"
    printf "  ${ADORE_REPO}/issues \n"
    printf "  or send us an email at: ${ADORE_SUPPORT_EMAIL_ADDRESS} \n"
    printf "\n\n"
    exit $exit_status
}

usage() {
  cat << EOF
Usage: $(basename "${BASH_SOURCE[0]}") [-h] [-v] [-f] -p param_value arg1 [arg2...]

Script description here.

Available options:

-h, --help                      Print this help and exit
-H, --headless                  Run ADORe installation in headless mode and non-interactive 
-s, --skip-prerequisite-checks  Do not run prerequisite checks for storage, os, etc 
-v, --verbose                   Print script debug info
EOF
  exit
}

function parse_params() {

  while :; do
    case "${1-}" in
    -h | --help) usage ;;
    -s | --skip-prerequisite-checks) SKIP_PREREQUISITE_CHECKS=1 ;;
    -v | --verbose) set -x ;;
    -H | --headless) HEADLESS=1 ;;
    -?*) exiterr "ERROR: Unknown option: $1" ;;
    *) break ;;
    esac
    shift
  done

  args=("$@")

  return 0
}


prompt_yes_no() {
    while true; do
        read -rp "Do you want to proceed? (yes/no): " choice
        case $choice in
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


banner(){

coffee_cup="
ADORe will be setup on your system. The following system changes will occurs:
  - Your OS version will be checked against supported Ubuntu versions: ${SUPPORTED_UBUNTU_VERSIONS// /, }
    Note: The only dependencies for ADORe are Docker and GNU Make; 
        however, this automated setup script is supported only on Ubuntu!
        For manual setup please refer to the help getting started help 
        guide: ${ADORE_HELP_LINK}/mkdocs/getting_started/getting_started/
  - Docker will be installed or updated using a setup script based off of 
        the official docker docs: https://docs.docker.com/engine/install/ubuntu/
  - APT dependencies 'GNU Make' and 'git' will be installed
  - ADORe (${ADORE_REPO}) will be cloned to: ${CLONE_DIR}/adore
  - ADORe will be built with \"make build\"
  - You may be prompted for sudo password (root priviliges are needed to install Docker, GNU Make, and git)

ADORe Requirements:
  - ADORe requires a minimum of ~${REQUIRED_FREESPACE_GB}GB of storage
    The setup requires downloading 10–20 GB of dependencies depending on configuration from the Ubuntu central APT repository(https://ubuntu.com/server/docs/package-management), Docker.io(https://www.docker.com/), and PyPI(https://pypi.org/) via pip.
    - Recent version of Docker (This setup script will install the latest version of Docker) 
  - This script is designed and tested for Ubuntu versions 20.04-24.04
 
Initial setup can take 10-15 minutes depending on system and internet connection.
   Grab a cup of coffee and wait for the setup to complete.

    ( (
     ) )
  ........
  |      |]
  \      / 
   \`'--'\`
"
    printf "%s\n" "$coffee_cup"
    if [[ $HEADLESS == 0 ]]; then 
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

        protocol=$(echo $url | sed 's|^\(.*://\).*|\1|')
        domain=$(echo $url | sed 's|https\?://||')

        if [[ "$protocol" == "https://" ]]; then
            port=443
        else
            port=80
        fi

        trap "" ERR
        { exec 3<>/dev/tcp/$domain/$port; } &>/dev/null


        if [ $? -eq 0 ]; then
            echo "    $url is reachable"
        else
            echoerr "   ERROR: $url is unreachable\n"
            echoerr "     Unable to reach $url. Please check your internet connection, firewall, or proxy.\n"
            exit 1
        fi
        exec 3>&-

        trap - ERR
    done
}

check_os_version(){
    local os_version=$(cat /etc/os-release | grep VERSION_ID | cut -d'"' -f2)

    if [[ $SUPPORTED_UBUNTU_VERSIONS != *"$os_version"* ]]; then
        exiterr "ERROR: unsupported os version: ${os_version} Supported versions: ${SUPPORTED_UBUNTU_VERSIONS}"
    fi
}

check_freespace(){
    freespace=$(df -h --output=avail . | tail -n 1 | awk '{print $1}' | sed "s|G||g")
    current_device=$(df --output=source . | tail -n 1)
    if (( $(echo "$freespace <= $REQUIRED_FREESPACE_GB" | bc -l) )); then     
        exiterr "ERROR: Not enough free space: ${freespace} available and: ${REQUIRED_FREESPACE_GB} required.\n Free up some space on '${current_device}' and try again."
    fi 
}

install_dependencies(){
    sudo apt-get update
    sudo apt-get install -y make git
}

install_docker(){
    bash <(curl -sSL https://raw.githubusercontent.com/eclipse-adore/adore/develop/tools/install_docker.sh)
}

clone_adore(){
    cd "${CLONE_DIR}"
    
    if [[ ! -d "adore" ]]; then
        git clone "${ADORE_REPO}"
    fi
    cd "${CLONE_DIR}/adore"
    cp .gitmodules .gitmodules.bak
    sed -i "s|git@github.com:|https://github.com/|g" .gitmodules
    git submodule update --init --recursive
    mv .gitmodules.bak .gitmodules
    git submodule sync
}

build_adore_cli(){
newgrp docker << END
    cd "${CLONE_DIR}/adore" && make build
END
newgrp docker << END
    cd "${CLONE_DIR}/adore" && make build_user_libraries
END

setup_complete=true
}



parse_params "$*"
banner
if [[ $SKIP_PREREQUISITE_CHECKS == 0 ]]; then
    check_resources
    check_freespace
    check_os_version
else
    printf "Prerequsite checks skipped...\n"
fi

install_dependencies
clone_adore
install_docker
build_adore_cli
get_help
