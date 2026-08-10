# Sourced by run_tests.sh and mqtt_test_remote.sh. Not executable on its own.

PASS=0
FAIL=0
SKIPPED=0
FAILED_CASES=()
BRIDGE_PID=""

banner() { printf '\n=== %s ===\n' "$1"; }

record() {
    local name="$1" status="$2" log="${3:-}"
    if [[ "$status" -eq 0 ]]; then
        echo "PASS: $name"
        PASS=$((PASS + 1))
    else
        echo "FAIL: $name" >&2
        [[ -n "$log" && -s "$log" ]] && sed 's/^/      /' "$log" >&2
        FAILED_CASES+=("$name")
        FAIL=$((FAIL + 1))
    fi
}

skip() {
    echo "SKIP: $1 ($2)"
    SKIPPED=$((SKIPPED + 1))
}

# Prints the first line of a payload, clipped, so a firehose topic cannot flood
# the test output.
show_payload() {
    local label="$1" file="$2"
    if [[ ! -s "$file" ]]; then
        echo "  $label: <nothing received>"
        return 1
    fi
    echo "  $label: $(head -c 300 "$file" | head -n 1)"
}

wait_for_port() {
    local host="$1" port="$2" limit="${3:-15}"
    local deadline=$((SECONDS + limit))
    while (( SECONDS < deadline )); do
        nc -z -w1 "$host" "$port" 2>/dev/null && return 0
        sleep 0.2
    done
    return 1
}

start_bridge() {
    local config="$1" logfile="$2" limit="${3:-30}"
    if ! command -v ros2 >/dev/null 2>&1; then
        return 2
    fi
    ros2 run mqtt_message_bridge bridge_node \
        --ros-args -p "config_path:=$config" > "$logfile" 2>&1 &
    BRIDGE_PID=$!
    local deadline=$((SECONDS + limit))
    while (( SECONDS < deadline )); do
        grep -q 'Connected to MQTT broker' "$logfile" && break
        kill -0 "$BRIDGE_PID" 2>/dev/null || break
        sleep 0.5
    done
    if ! grep -q 'Connected to MQTT broker' "$logfile"; then
        return 1
    fi
    sleep 2
    return 0
}

stop_bridge() {
    [[ -z "$BRIDGE_PID" ]] && return 0
    kill "$BRIDGE_PID" 2>/dev/null
    wait "$BRIDGE_PID" 2>/dev/null
    BRIDGE_PID=""
}

# Lets a nested suite fold its counts into the parent's summary.
export_results() {
    [[ -n "${RESULTS_FILE:-}" ]] || return 0
    {
        printf '%s %s %s\n' "$PASS" "$FAIL" "$SKIPPED"
        [[ ${#FAILED_CASES[@]} -gt 0 ]] && printf '%s\n' "${FAILED_CASES[@]}"
    } > "$RESULTS_FILE"
}

absorb_results() {
    local file="$1"
    [[ -s "$file" ]] || return 0
    local p f s
    read -r p f s < "$file"
    PASS=$((PASS + p))
    FAIL=$((FAIL + f))
    SKIPPED=$((SKIPPED + s))
    while IFS= read -r case_name; do
        [[ -n "$case_name" ]] && FAILED_CASES+=("$case_name")
    done < <(tail -n +2 "$file")
}

summary() {
    export_results
    banner "Summary"
    echo "$PASS passed, $FAIL failed, $SKIPPED skipped"
    if (( FAIL > 0 )); then
        printf 'failed: %s\n' "${FAILED_CASES[*]}" >&2
        return 1
    fi
    return 0
}
