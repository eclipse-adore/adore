#!/usr/bin/env bash

SCRIPT_DIRECTORY="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

find_ros2_workspace() {
  current_dir="${SCRIPT_DIRECTORY}"

  while [ "$current_dir" != "/" ]; do
    if [ -d "$current_dir/build" ] && \
       [ -d "$current_dir/install" ] && \
       [ -d "$current_dir/log" ] && \
       [ -d "$current_dir/src" ]; then
      echo "$current_dir"
      return 0
    fi

    current_dir=$(dirname "$current_dir")
  done

  echo "Error: ROS 2 workspace not found." >&2
  return 1
}
ros2_package=$(grep -oP '<name>\K[^<]*' "${SCRIPT_DIRECTORY}/package.xml" | tr -d '[:space:]')
ros2_workspace=$(find_ros2_workspace)




(
cd ${ros2_workspace}
node=${ros2_package}
source "${ros2_workspace}/install/setup.bash"

if [[ -z $(ros2 pkg list | grep "${ros2_package}") ]]; then
    echo "ERROR: ROS2 Package: '${ros2_package}' not found. Did you build it?" >&2
    exit 1
fi

ros2 run ${ros2_package} ${node}
)


