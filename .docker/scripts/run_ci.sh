#!/usr/bin/env bash
# Convenience wrapper: run tests + docs locally using the CI Docker image.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=/dev/null
source "${SCRIPT_DIR}/common.sh"

require_host "CI convenience wrapper should be run on the host."

"${SCRIPT_DIR}/run_tests.sh"
"${SCRIPT_DIR}/run_docs.sh"
