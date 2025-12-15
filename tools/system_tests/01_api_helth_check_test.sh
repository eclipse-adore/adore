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

01_api_health_check_test() {
  local action=health_check
  local name="API Health Check Test"
  local description="This test validates that the API is responding correctly to basic requests."
  local status=""
  local message=""
  local api_health_output_json_file="${LOG_DIRECTORY}/api_health_check_results.json"

  printf "\n"
  printf "  Test: %s\n" "${name}"
  printf "    Description: %s\n" "${description}"
  printf "      This test aims to answer the following questions: \n"
  printf "        Is the API server responding?\n"
  printf "        Are the basic endpoints accessible?\n"
  printf "        Do the endpoints return valid JSON?\n"
  printf "    Starting API health check...\n"

  just api_start > /dev/null 2>&1

  printf "    Waiting for API to be ready...\n"
  if ! wait_for_api_ready; then
    printf "    Status: %s - API not ready after %s seconds\n" "$(bold "$(red "FAILED")")" "${API_READINESS_TIMEOUT}"
    return 1
  fi

  # Test 1: Status endpoint
  printf "    Testing status endpoint...\n"
  local status_http_code status_exit_code
  status_http_code=$(curl -s --max-time 10 -o /tmp/status_response -w "%{http_code}" http://localhost:8888/api/status)
  status_exit_code=$?

  if [ "$status_exit_code" -ne 0 ]; then
    printf "    Status: %s - Status endpoint failed with exit code %s\n" "$(bold "$(red "FAILED")")" "$status_exit_code"
    return 1
  fi

  if [ "$status_http_code" != "200" ]; then
    printf "    Status: %s - Status endpoint returned HTTP %s\n" "$(bold "$(red "FAILED")")" "$status_http_code"
    printf "    Response: %s\n" "$(cat /tmp/status_response)"
    return 1
  fi

  local status_result
  status_result=$(cat /tmp/status_response)
  # Validate status response is valid JSON
  if ! echo "$status_result" | jq . > /dev/null 2>&1; then
    printf "    Status: %s - Status endpoint returned invalid JSON\n" "$(bold "$(red "FAILED")")"
    printf "    Response: %s\n" "$status_result"
    return 1
  fi

  # Test 2: Scenario endpoint
  printf "    Testing scenario endpoints...\n"
  local scenario_http_code scenario_exit_code scenario_result
  scenario_http_code=$(curl -s --max-time 10 -o /tmp/scenario_response -w "%{http_code}" http://localhost:8888/api/scenario/get)
  scenario_exit_code=$?

  if [ "$scenario_exit_code" -ne 0 ]; then
    printf "    Status: %s - Scenario endpoint failed with exit code %s\n" "$(bold "$(red "FAILED")")" "$scenario_exit_code"
    return 1
  fi

  if [ "$scenario_http_code" != "200" ]; then
    printf "    Status: %s - Scenario endpoint returned HTTP %s\n" "$(bold "$(red "FAILED")")" "$scenario_http_code"
    printf "    Response: %s\n" "$(cat /tmp/scenario_response)"
    return 1
  fi

  scenario_result=$(cat /tmp/scenario_response)
  # Validate scenario response is valid JSON
  if ! echo "$scenario_result" | jq . > /dev/null 2>&1; then
    printf "    Status: %s - Scenario endpoint returned invalid JSON\n" "$(bold "$(red "FAILED")")"
    printf "    Response: %s\n" "$scenario_result"
    return 1
  fi

  # Test 3: Test invalid endpoint returns proper error
  printf "    Testing error handling...\n"
  local error_http_code error_exit_code
  error_http_code=$(curl -s --max-time 10 -o /dev/null -w "%{http_code}" http://localhost:8888/api/nonexistent)
  error_exit_code=$?

  if [ "$error_exit_code" -ne 0 ]; then
    printf "    Status: %s - Error test failed with exit code %s\n" "$(bold "$(red "FAILED")")" "$error_exit_code"
    return 1
  fi

  # Check that we get a 404 for non-existent endpoint
  if [ "$error_http_code" != "404" ]; then
    printf "    Status: %s - Expected 404 for non-existent endpoint, got %s\n" "$(bold "$(red "FAILED")")" "$error_http_code"
    return 1
  fi

  printf "\n"
  printf "    Compiling results...\n"

  # Create summary JSON
  local health_summary
  health_summary=$(jq -n \
    --arg status_response "$status_result" \
    --arg scenario_response "$scenario_result" \
    --arg status_http_code "$status_http_code" \
    --arg scenario_http_code "$scenario_http_code" \
    --arg error_http_code "$error_http_code" \
    '{
            "test_name": "API Health Check",
            "timestamp": now | strftime("%Y-%m-%d %H:%M:%S"),
            "results": {
                "status_endpoint": {
                    "status": "PASSED",
                    "http_code": $status_http_code,
                    "response": ($status_response | fromjson)
                },
                "scenario_endpoint": {
                    "status": "PASSED",
                    "http_code": $scenario_http_code,
                    "response_length": ($scenario_response | length)
                },
                "error_handling": {
                    "status": "PASSED",
                    "http_code": $error_http_code
                }
            },
            "overall_status": "PASSED"
        }')

  echo "$health_summary" > "$api_health_output_json_file"

  # Extract key info for display
  local api_version
  api_version=$(echo "$status_result" | jq -r '.version // "unknown"' 2> /dev/null)

  message="        API Health Check Summary:
            Status endpoint: PASSED (HTTP $status_http_code)
            Scenario endpoint: PASSED (HTTP $scenario_http_code)
            Error handling: PASSED (proper 404 response)
            API version: ${api_version}"

  status=$(bold "$(green "PASSED")")
  printf "    Message:\n%s\n" "$message"
  printf "    %-77s %s\n" "Status:" "${status}"
  printf "    See the health check log for more info: %s\n" "$api_health_output_json_file"

  # Clean up temp files
  rm -f /tmp/status_response /tmp/scenario_response

  return 0
}
