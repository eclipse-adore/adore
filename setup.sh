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
SCRIPT_DIRECTORY="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
ROS2_WORKSPACE_DIRECTORY="$(realpath "${SCRIPT_DIRECTORY}/ros2_workspace")"
if [ ! -f /.dockerenv ]; then
    echo "ERROR: This script must be sourced inside the ADORe CLI context." >&2
    return 1
fi

if [ -z "${DISPLAY:-}" ]; then
    [ -f /tmp/.adore_display ] && source /tmp/.adore_display 2>/dev/null || export DISPLAY=:99
fi

if [[ "$SHELL" == *"bash"* ]]; then
    LOCAL_SETUP_SCRIPT="${ROS2_WORKSPACE_DIRECTORY}/install/local_setup.bash"
    ROS_SETUP_SCRIPT="/opt/ros/${ROS_DISTRO}/setup.bash"
elif [[ "$SHELL" == *"zsh"* ]]; then
    LOCAL_SETUP_SCRIPT="${ROS2_WORKSPACE_DIRECTORY}/install/local_setup.zsh"
    ROS_SETUP_SCRIPT="/opt/ros/${ROS_DISTRO}/setup.zsh"
else
    echo shell $SHELL
    echo "ERROR: Unsupported shell: $SHELL" >&2
    return 1
fi
bash ${SCRIPT_DIRECTORY}/tools/check_adore_binaries.sh
printf "\n"
source "$ROS_SETUP_SCRIPT"
if [[ "${BASH_SOURCE[0]}" != "${0}" ]]; then
    if [[ -f "${LOCAL_SETUP_SCRIPT}" ]]; then
        set -a
        source "${LOCAL_SETUP_SCRIPT}"
        set +a
        echo "Sourced ${LOCAL_SETUP_SCRIPT} environment"
    else
        echo "WARNING: ${LOCAL_SETUP_SCRIPT} does not exist. Did you build the ROS workspace?"
        echo "    To build the ROS nodes with 'cd ros2_workspace && make build' inside the ADORe CLI." >&2
    fi
else
    echo "ERROR: script designed to be sourced. Call again with 'source setup.sh'" >&2
    return 1
fi
source /opt/adore_venv/bin/activate

source "${SCRIPT_DIRECTORY}/adore.env"
PYVER=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
export PYTHONPATH="/opt/adore_venv/lib/python${PYVER}/site-packages:/usr/lib/python3/dist-packages:${PYTHONPATH}"

bash ${SCRIPT_DIRECTORY}/tools/adore_api/adore_api.sh
