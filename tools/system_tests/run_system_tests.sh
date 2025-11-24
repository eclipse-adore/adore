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
just api_start > /dev/null 2>&1
# Directory of this runner script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Directory containing the test files
# If an argument is given:
#   - absolute path is used as-is
#   - relative path is resolved relative to SCRIPT_DIR
if [[ $# -ge 1 ]]; then
  if [[ "$1" = /* ]]; then
    TEST_DIR="$1"
  else
    TEST_DIR="${SCRIPT_DIR}/$1"
  fi
else
  TEST_DIR="${SCRIPT_DIR}"
fi

# Where logs go
LOG_DIRECTORY="${LOG_DIRECTORY:-.log}"
mkdir -p "${LOG_DIRECTORY}"

# Load helpers first
if [[ -f "${TEST_DIR}/test_helpers.sh" ]]; then
  # shellcheck source=/dev/null
  . "${TEST_DIR}/test_helpers.sh"
else
  echo "ERROR: Missing ${TEST_DIR}/test_helpers.sh" >&2
  exit 1
fi

# Source all *_test.sh files
shopt -s nullglob
for file in "${TEST_DIR}"/*_test.sh; do
  # shellcheck source=/dev/null
  . "$file"
done
shopt -u nullglob

# Collect all functions that end in _test
mapfile -t TEST_FUNCTIONS < <(compgen -A function | grep '_test$' | sort)

if [[ "${#TEST_FUNCTIONS[@]}" -eq 0 ]]; then
  echo "No *_test functions found in ${TEST_DIR}." >&2
  exit 1
fi

echo "Discovered tests in ${TEST_DIR}:"
for t in "${TEST_FUNCTIONS[@]}"; do
  echo "  - ${t}"
done
echo

overall_status=0

for t in "${TEST_FUNCTIONS[@]}"; do
  echo "=== Running test: ${t} ==="
  # Run each test in a subshell so a 'return 1' or 'exit' inside doesn't kill the runner
  if ( "$t" ); then
    echo "=== ${t}: PASSED ==="
  else
    echo "=== ${t}: FAILED ==="
    overall_status=1
  fi
  echo
done
just api_stop > /dev/null 2>&1
exit "${overall_status}"
