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

02_simulation_test_scenario_test() {
  local action=simulate
  local name="Simulation Test"
  local description="This test executes the simulation_test.launch.py scenario and verify the model checking results."
  local status=""
  local message=""
  local model_checking_output_json_file="${LOG_DIRECTORY}/simulation_test_model_checking_results.json"

  printf "\n"
  printf "  Test: %s\n" "${name}"
  printf "    Description: %s\n" "${description}"
  printf "      This test aims to answer the following questions: \n"
  printf "        Did the vehicle move?\n"
  printf "        Did the vehicle reach its goal?\n"
  printf "        Did the scenario generate any exceptions?\n"
  printf "    Running scenario...\n"

  printf "    Waiting for API to be ready...\n"
  if ! wait_for_api_ready; then
    printf "    Status: %s - API not ready after %s seconds\n" "$(bold "$(red "FAILED")")" "${API_READINESS_TIMEOUT}"
    return 1
  fi
  printf "    API Ready...\n"


  {
    while true; do
      sleep 1
      printf "." >&2
    done
  } &
  local dot_pid=$!

  local result curl_exit_code
  result=$(curl -s --max-time 50 -X POST http://localhost:8888/api/scenario/start/model_checked \
            -H "Content-Type: application/json" \
            -d '{"duration":30}')
  curl_exit_code=$?

  kill "$dot_pid" 2> /dev/null
  wait "$dot_pid" 2> /dev/null || true

  if [ "$curl_exit_code" -eq 28 ]; then
    printf "\n"
    printf "    Status: %s - Request timed out after 20 seconds\n" "$(bold "$(red "FAILED")")"
    return 1
  elif [ "$curl_exit_code" -ne 0 ]; then
    printf "\n"
    printf "    Status: %s - Request failed with exit code %s\n" "$(bold "$(red "FAILED")")" "$curl_exit_code"
    return 1
  fi

  printf "\n"
  printf "    Parsing results...\n"
  echo "${result}" > "${model_checking_output_json_file}"

  if [ -z "$result" ] || [ "$result" = "null" ]; then
    printf "    Status: %s - API returned no results\n" "$(bold "$(red "FAILED")")"
    return 1
  fi

  if ! echo "$result" | jq . > /dev/null 2>&1; then
    printf "    Status: %s - API returned invalid JSON\n" "$(bold "$(red "FAILED")")"
    printf "    Response: %s\n" "$result"
    return 1
  fi

  if ! echo "$result" | jq -e '.model_check_result.results' > /dev/null 2>&1; then
    printf "    Status: %s - API response missing expected model check results\n" "$(bold "$(red "FAILED")")"
    printf "    Response: %s\n" "$result"
    return 1
  fi

  message=$(echo "$result" | jq -r '
      .model_check_result.results.SUMMARY as $s |
      (
        "        Model Check Summary: " +
        (($s.total_propositions // $s.analyzed // 0) | tostring) + " analyzed, " +
        (($s.passed // 0) | tostring) + " passed, " +
        (($s.failed // 0) | tostring) + " failed, success rate: " +
        (((($s.success_rate // 0) * 100) | round) | tostring) + "% - Overall result: " +
        ($s.overall_result // "UNKNOWN") +
        "\n"
      ) +
      "            Propositions:\n" +
      (
        (.model_check_result.results // {})
        | to_entries
        | map(select(.key != "SUMMARY"))
        | map(
          "                " + (.value.description.title // .value.title // .key) + ": " + (.value.status // "UNKNOWN") + "\n" +
          "                    Description: " + (.value.description.description // .value.description // "N/A") + "\n" +
          "                    Safety Goal: " + (.value.description.safety_rationale // .value.safety_rationale // "N/A") + "\n" +
          "                    Formula Description: " + (.value.formula_description // "N/A") + "\n" +
          "                    Formula Type: " + (.value.formula_type // "N/A")
        )
        | join("\n\n")
      )
    ')

  local model_checking_status
  model_checking_status=$(echo "$result" | jq -r '
      if ((.model_check_result.results.SUMMARY.success_rate // 0) == 1 and 
          ([.model_check_result.results | to_entries[] | select(.key != "SUMMARY") | .value.status] | 
           any(. == "NO_DATA" or . == "FAIL")) | not) then 0 else 1 end
    ')

  if [ "$model_checking_status" -eq 0 ]; then
    status=$(bold "$(green "PASSED")")
  else
    status=$(bold "$(red "FAILED")")
  fi

  printf "    Message:\n%s\n" "$message"
  printf "    %-77s %s\n" "Status:" "${status}"
  just api_stop > /dev/null 2>&1
  printf "    See the model checking log for more info: %s\n" "$model_checking_output_json_file"

  return "$model_checking_status"
}
