#!/usr/bin/env bash
# Ensure .colcon_workspace/src mirrors the top-level package layout via symlinks.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=/dev/null
source "${SCRIPT_DIR}/common.sh"

SRC_DIR="${WORKSPACE_ROOT}/.colcon_workspace/src"
mkdir -p "${SRC_DIR}"

# Top-level dirs that contain colcon packages
CATEGORIES=(
  "adore_scenarios"
  "ros2_conversions"
  "interfaces"
  "libraries"
  "ros2_nodes"
  "ros2_messages"
  "vendor"
)

link_category() {
  local category="$1"

  local target_dir="${WORKSPACE_ROOT}/${category}"
  if [[ ! -d "${target_dir}" ]]; then
    echo "WARN: Skipping category '${category}' – directory not found at ${target_dir}" >&2
    return 0
  fi

  local link_path="${SRC_DIR}/${category}"
  local target_rel="../../${category}"

  if [[ -L "${link_path}" ]]; then
    # Already a symlink – check if it points to the expected location
    local current
    current="$(readlink "${link_path}")"
    if [[ "${current}" == "${target_rel}" ]]; then
      echo "OK: Symlink for '${category}' already correct."
      return 0
    else
      echo "Updating symlink for '${category}': ${current} -> ${target_rel}"
      rm -f "${link_path}"
    fi
  fi

  if [[ -e "${link_path}" ]]; then
    echo "ERROR: ${link_path} exists and is not a symlink. Please remove or rename it." >&2
    return 1
  fi

  echo "Creating symlink: ${link_path} -> ${target_rel}"
  ln -sfn "${target_rel}" "${link_path}"
}

for cat in "${CATEGORIES[@]}"; do
  link_category "${cat}"
done
