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

03_eclipse_due_diligence_scan_test() {
    local action=due_diligence_scan
    local name="Eclipse Due Diligence Scan Test"
    local description="This test runs 'just due_diligence_scan' and validates the scan output."
    local status=""
    local message=""
    local scan_log_file="${LOG_DIRECTORY}/due_diligence_scan.log"

    printf "\n"
    printf "  Test: %s\n" "${name}"
    printf "    Description: %s\n" "${description}"
    printf "      This test runs the eclipse due diligence scanner to verify all source code has the proper license header comment. \n"
    printf "    Starting just due_diligence_scan...\n"

    if ! just due_diligence_scan >"$scan_log_file" 2>&1; then
        status=$(bold "$(red "FAILED")")
        message="        just due_diligence_scan command failed. See log: ${scan_log_file}"
        cat "${scan_log_file}"
        printf "    Message:\n%s\n" "$message"
        printf "    %-77s %s\n" "Status:" "${status}"
        return 1
    fi

    status=$(bold "$(green "PASSED")")
    message="        just due_diligence_scan succeeded. Tail of log shown below:"
    printf "    Message:\n%s\n" "$message"
    tail -15 "${scan_log_file}"
    printf "    %-77s %s\n" "Status:" "${status}"
    printf "    See the due_diligence_scan log for full details: %s\n" "$scan_log_file"

    return 0
}
