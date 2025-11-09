#!/usr/bin/env bash
set -euo pipefail

# Resolve repo root = two levels up from this script (.docker/scripts)
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SRC_DIR="${REPO_ROOT}/.colcon_workspace/src"

mkdir -p "${SRC_DIR}"

# Top-level dirs you moved out of colcon_workspace/src
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
  local target_rel="../../${category}"          # relative from colcon_workspace/src
  local target_abs="${REPO_ROOT}/${category}"
  local link_path="${SRC_DIR}/${category}"

  if [ ! -d "${target_abs}" ]; then
    echo "Warning: ${target_abs} does not exist, skipping" >&2
    return
  fi

  if [ -L "${link_path}" ]; then
    # Existing symlink: check target
    local current
    current="$(readlink "${link_path}")"
    if [ "${current}" = "${target_rel}" ]; then
      echo "Symlink already correct: ${link_path} -> ${current}"
      return
    else
      echo "Updating symlink: ${link_path} (was ${current}, now ${target_rel})"
      ln -sfn "${target_rel}" "${link_path}"
      return
    fi
  fi

  if [ -e "${link_path}" ]; then
    echo "ERROR: ${link_path} exists and is not a symlink. Please remove or rename it." >&2
    return 1
  fi

  echo "Creating symlink: ${link_path} -> ${target_rel}"
  ln -sfn "${target_rel}" "${link_path}"
}

for cat in "${CATEGORIES[@]}"; do
  link_category "${cat}"
done
