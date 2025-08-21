SCRIPT_DIRECTORY="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
ROS2_WORKSPACE_DIRECTORY="$(realpath "${SCRIPT_DIRECTORY}/ros2_workspace")"


if [[ "$SHELL" == *"bash"* ]]; then
    LOCAL_SETUP_SCRIPT="${ROS2_WORKSPACE_DIRECTORY}/install/local_setup.bash"
    ROS_SETUP_SCRIPT="/opt/ros/${ROS_DISTRO}/setup.bash"
elif [[ "$SHELL" == *"zsh"* ]]; then
    LOCAL_SETUP_SCRIPT="${ROS2_WORKSPACE_DIRECTORY}/install/local_setup.zsh"
    ROS_SETUP_SCRIPT="/opt/ros/${ROS_DISTRO}/setup.zsh"
else
    echo shell $SHELL
    echo "Unsupported shell: $SHELL" >&2
    exit 1
fi

source "$ROS_SETUP_SCRIPT"

if [[ "${BASH_SOURCE[0]}" != "${0}" ]]; then
    if [[ -f "${LOCAL_SETUP_SCRIPT}" ]]; then
        set -a
        source "${LOCAL_SETUP_SCRIPT}"
        set +a
        echo "Sourced ${LOCAL_SETUP_SCRIPT} environment"
    else
        echo "WARNING: ${LOCAL_SETUP_SCRIPT} does not exist. Did you build the ROS nodes?"
        echo "    To build the ROS nodes with 'cd ros2_workspace && make build' inside the ADORe CLI." >&2
    fi
else
    echo "ERROR: script designed to be sourced. Call again with 'source setup.sh'" >&2
    exit 1
fi

source ${SCRIPT_DIRECTORY}/tools/adore_api/adore_api.sh
