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

# Common helpers for system/integration tests

# Where logs go; runner usually sets this, but default just in case.
LOG_DIRECTORY="${LOG_DIRECTORY:-.log}"

# Global timeout for API readiness check (in seconds)
API_READINESS_TIMEOUT="${API_READINESS_TIMEOUT:-10}"

# Provide simple color helpers if they don't already exist
if ! declare -F bold >/dev/null 2>&1; then
  bold()   { printf '\033[1m%s\033[0m' "$*"; }
fi
if ! declare -F red >/dev/null 2>&1; then
  red()    { printf '\033[31m%s\033[0m' "$*"; }
fi
if ! declare -F green >/dev/null 2>&1; then
  green()  { printf '\033[32m%s\033[0m' "$*"; }
fi

# Wait until the API status endpoint responds with HTTP 200 or timeout
wait_for_api_ready() {
  local timeout=${1:-$API_READINESS_TIMEOUT}
  local status_url="http://localhost:8888/api/status"
  local elapsed=0

  while [ "$elapsed" -lt "$timeout" ]; do
    # First check that we can reach the endpoint at all
    if curl -s --max-time 5 "$status_url" >/dev/null 2>&1; then
      # Then check the HTTP status code explicitly
      local http_code
      http_code=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 "$status_url")
      if [ "$http_code" = "200" ]; then
        return 0
      fi
    fi

    sleep 1
    elapsed=$((elapsed + 1))
  done

  return 1
}