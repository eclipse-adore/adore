#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec "${SCRIPT_DIR}/start.sh" \
    /bin/bash -c 'source /ros2_workspace_dist/install/setup.bash && cd /ros2_workspace_dist/adore_scenarios/simulation_scenarios && exec /bin/bash'
