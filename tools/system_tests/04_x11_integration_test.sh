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

04_x11_integration_test() {
    local action=x11_integration_test
    local name="X11 Integration Test"
    local description="This test validates X11 forwarding is working by launching a GUI application."
    local status=""
    local message=""
    local test_window="xeyes"
    local xeyes_pid=""

    printf "\n"
    printf "  Test: %s\n" "${name}"
    printf "    Description: %s\n" "${description}"
    printf "      This test aims to answer the following questions: \n"
    printf "        Is DISPLAY variable properly set?\n"
    printf "        Can GUI applications connect to the X11 server?\n"
    printf "        Are windows actually visible on the host display?\n"
    printf "    Assumption: running inside a Docker container with X11 forwarded.\n"

    # 1) Check DISPLAY is set
    if [[ -z "${DISPLAY:-}" ]]; then
        status=$(bold "$(red "FAILED")")
        message="        DISPLAY variable is not set. X11 forwarding is not configured in this container."
        printf "    Message:\n%s\n" "$message"
        printf "    %-77s %s\n" "Status:" "${status}"
        return 1
    fi

    printf "    DISPLAY is set to '%s'\n" "${DISPLAY}"

    # 2) Check we can talk to the X server (best effort)
    if command -v xdpyinfo >/dev/null 2>&1; then
        if ! xdpyinfo >/dev/null 2>&1; then
            status=$(bold "$(red "FAILED")")
            message="        Could not query X server with xdpyinfo. X11 connection appears broken."
            printf "    Message:\n%s\n" "$message"
            printf "    %-77s %s\n" "Status:" "${status}"
            return 1
        fi
    elif command -v xset >/dev/null 2>&1; then
        if ! xset q >/dev/null 2>&1; then
            status=$(bold "$(red "FAILED")")
            message="        Could not query X server with xset. X11 connection appears broken."
            printf "    Message:\n%s\n" "$message"
            printf "    %-77s %s\n" "Status:" "${status}"
            return 1
        fi
    else
        printf "    WARNING: Neither 'xdpyinfo' nor 'xset' is installed; skipping low-level X server query.\n"
    fi

    # 3) Ensure required GUI tools are present
    if ! command -v "${test_window}" >/dev/null 2>&1; then
        status=$(bold "$(red "FAILED")")
        message=$(
          cat <<EOF
        '${test_window}' is not installed in the container.
        Install it (e.g. on Debian/Ubuntu: 'apt-get update && apt-get install -y x11-apps')
        and re-run this test.
EOF
        )
        printf "    Message:\n%s\n" "$message"
        printf "    %-77s %s\n" "Status:" "${status}"
        return 1
    fi

    if ! command -v xwininfo >/dev/null 2>&1; then
        status=$(bold "$(red "FAILED")")
        message=$(
          cat <<EOF
        'xwininfo' is not installed in the container.
        Install it (e.g. on Debian/Ubuntu: 'apt-get update && apt-get install -y x11-utils')
        and re-run this test.
EOF
        )
        printf "    Message:\n%s\n" "$message"
        printf "    %-77s %s\n" "Status:" "${status}"
        return 1
    fi

    printf "    Starting X11 integration test (launching '%s')...\n" "${test_window}"

    # 4) Launch test GUI application in the background
    "${test_window}" >/dev/null 2>&1 &
    xeyes_pid=$!

    # Give the window some time to appear
    sleep 3

    # 5) Capture xwininfo output without letting a non-zero exit code kill the test
    local xwin_tree
    xwin_tree="$(xwininfo -tree -root 2>/dev/null || true)"

    if ! printf '%s\n' "${xwin_tree}" | grep -qi "${test_window}"; then
        status=$(bold "$(red "FAILED")")
        message="        GUI window '${test_window}' not found in X11 window tree."
        printf "    Message:\n%s\n" "$message"
        printf "    Sample of xwininfo -tree -root (first 30 lines):\n"
        printf '%s\n' "${xwin_tree}" | head -n 30
        printf "    %-77s %s\n" "Status:" "${status}"

        # Attempt to clean up the test application
        if [[ -n "${xeyes_pid}" ]]; then
            kill "${xeyes_pid}" >/dev/null 2>&1 || true
        fi
        pkill "${test_window}" >/dev/null 2>&1 || true

        return 1
    fi

    # 6) Clean up test application
    if [[ -n "${xeyes_pid}" ]]; then
        kill "${xeyes_pid}" >/dev/null 2>&1 || true
    fi
    pkill "${test_window}" >/dev/null 2>&1 || true

    status=$(bold "$(green "PASSED")")
    message="        X11 integration working. GUI window '${test_window}' was successfully displayed and detected via xwininfo."
    printf "    Message:\n%s\n" "$message"
    printf "    %-77s %s\n" "Status:" "${status}"

    return 0
}
