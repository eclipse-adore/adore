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


SCRIPT_DIRECTORY="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
ADORE_DIRECTORY="$(realpath "${SCRIPT_DIRECTORY}/..")"

source "${ADORE_DIRECTORY}/adore.env"


# ros_topic_benchmark.sh - ROS2 Topic Rate Benchmarking Script

set -e  

# Configurations
DEFAULT_TOPIC="/ego_vehicle/vehicle_state/dynamic"
SCENARIO_BASE_PATH="${ADORE_DIRECTORY}/adore_scenarios/simulation_scenarios"
WAIT_TIME=10
BENCHMARK_DURATION=10
TOPIC_READY_TIMEOUT=30  # Maximum time to wait for topic to start publishing

# Environment variables with defaults
ROS_BENCHMARK_TOPIC=${ROS_BENCHMARK_TOPIC:-$DEFAULT_TOPIC}
ROS_BENCHMARK_SCENARIO=${ROS_BENCHMARK_SCENARIO:-"simulation_test.launch.py"}
ROS_BENCHMARK_MIN_RATE=${ROS_BENCHMARK_MIN_RATE:-10}
ROS_BENCHMARK_MAX_JITTER=${ROS_BENCHMARK_MAX_JITTER:-0.04}
ROS_BENCHMARK_MAX_STD=${ROS_BENCHMARK_MAX_STD:-0.014}

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to cleanup background processes
cleanup() {
    if [ ! -z "$SCENARIO_PID" ]; then
        print_info "Cleaning up scenario process (PID: $SCENARIO_PID)"
        kill $SCENARIO_PID 2>/dev/null || true
        wait $SCENARIO_PID 2>/dev/null || true
    fi
}

# Set trap for cleanup on exit
trap cleanup EXIT

# Function to wait for topic to start publishing
# Function to wait for topic to start publishing
wait_for_topic_publishing() {
    local topic="$1"
    local timeout="$2"
    local start_time=$(date +%s)
    local temp_check=$(mktemp)
    
    print_info "Waiting for topic to start publishing: $topic"
    
    while [ $(($(date +%s) - start_time)) -lt $timeout ]; do
        # Try to get a few messages from the topic with a short timeout
        timeout 3 ros2 topic hz "$topic" > "$temp_check" 2>&1 || true
        
        # Check if we got valid rate data (indicates topic is publishing)
        if grep -q "average rate:" "$temp_check"; then
            # We got valid rate data, topic is publishing
            rm -f "$temp_check"
            print_info "Topic is now publishing: $topic"
            return 0
        fi
        
        # Check if it's just the "not published yet" warning
        if grep -q "WARNING.*does not appear to be published yet" "$temp_check"; then
            printf "."
            sleep 2
        else
            # Some other error occurred - check if topic exists at all
            if ! ros2 topic list | grep -q "^${topic}$"; then
                print_error "Topic $topic does not exist"
                rm -f "$temp_check"
                return 1
            fi
            printf "."
            sleep 2
        fi
    done
    
    printf "\n"
    print_error "Topic did not start publishing within $timeout seconds"
    rm -f "$temp_check"
    return 1
}

# Validate inputs
if [ -z "$ROS_BENCHMARK_SCENARIO" ]; then
    print_error "ROS_BENCHMARK_SCENARIO environment variable is required"
    echo "Usage: ROS_BENCHMARK_SCENARIO=<scenario_name> ROS_BENCHMARK_TOPIC=<topic_name> $0"
    exit 1
fi

# Check if scenario file exists
SCENARIO_PATH="${SCENARIO_BASE_PATH}/${ROS_BENCHMARK_SCENARIO}"
if [ ! -f "$SCENARIO_PATH" ] && [ ! -f "${SCENARIO_PATH}.launch.py" ] && [ ! -f "${SCENARIO_PATH}.launch" ]; then
    print_error "Scenario not found: $SCENARIO_PATH"
    print_info "Looking for scenarios in: $SCENARIO_BASE_PATH"
    ls -la "$SCENARIO_BASE_PATH" 2>/dev/null || print_warning "Scenario directory not found"
    exit 1
fi

print_info "Starting ROS2 Message Benchmark"
print_info "Topic: $ROS_BENCHMARK_TOPIC"
print_info "Scenario: $ROS_BENCHMARK_SCENARIO"
print_info "Scenario Path: $SCENARIO_PATH"
print_info "Benchmark Thresholds:"
print_info "  Min Rate: ${ROS_BENCHMARK_MIN_RATE} Hz"
print_info "  Max Jitter: ${ROS_BENCHMARK_MAX_JITTER}s"
print_info "  Max Std Dev: ${ROS_BENCHMARK_MAX_STD}s"

# Launch the scenario in background with no output
print_info "Launching scenario in background..."
if [ -f "${SCENARIO_PATH}.launch.py" ]; then
    ros2 launch "${SCENARIO_PATH}.launch.py" > /dev/null 2>&1 &
elif [ -f "${SCENARIO_PATH}.launch" ]; then
    ros2 launch "${SCENARIO_PATH}.launch" > /dev/null 2>&1 &
else
    # Assume it's a Python launch file without extension
    ros2 launch "$SCENARIO_PATH" > /dev/null 2>&1 &
fi

SCENARIO_PID=$!
print_info "Scenario launched with PID: $SCENARIO_PID"

# Wait for scenario to start
print_info "Waiting ${WAIT_TIME} seconds for scenario to initialize..."
sleep $WAIT_TIME

# Check if scenario is still running
if ! kill -0 $SCENARIO_PID 2>/dev/null; then
    print_error "Scenario process has died unexpectedly"
    exit 1
fi

# Check if topic exists first
print_info "Checking if topic exists: $ROS_BENCHMARK_TOPIC"
if ! ros2 topic list | grep -q "^${ROS_BENCHMARK_TOPIC}$"; then
    print_error "Topic $ROS_BENCHMARK_TOPIC is not available"
    print_info "Available topics:"
    ros2 topic list
    exit 1
fi

# Wait for topic to start publishing with retry logic
if ! wait_for_topic_publishing "$ROS_BENCHMARK_TOPIC" "$TOPIC_READY_TIMEOUT"; then
    print_error "Topic $ROS_BENCHMARK_TOPIC failed to start publishing"
    exit 1
fi

# Run ros2 topic hz and capture output
print_info "Starting benchmark on topic: $ROS_BENCHMARK_TOPIC"
print_info "Benchmark duration: ${BENCHMARK_DURATION} seconds"

# Create a temporary file to capture output
TEMP_OUTPUT=$(mktemp)
trap "rm -f $TEMP_OUTPUT; cleanup" EXIT

# Run ros2 topic hz with timeout
timeout ${BENCHMARK_DURATION} ros2 topic hz "$ROS_BENCHMARK_TOPIC" > "$TEMP_OUTPUT" 2>&1 || {
    exit_code=$?
    if [ $exit_code -eq 124 ]; then
        print_info "Benchmark completed (timeout reached)"
    else
        print_error "ros2 topic hz failed with exit code: $exit_code"
        cat "$TEMP_OUTPUT"
        exit 1
    fi
}

# Check if the output indicates the topic stopped publishing during the benchmark
if grep -q "WARNING.*does not appear to be published yet" "$TEMP_OUTPUT"; then
    # Count how many times this warning appears
    warning_count=$(grep -c "WARNING.*does not appear to be published yet" "$TEMP_OUTPUT" || echo "0")
    
    # If it appears more than a few times, it's likely a real issue
    if [ "$warning_count" -gt 3 ]; then
        print_error "Topic $ROS_BENCHMARK_TOPIC stopped publishing during benchmark"
        print_error "Warning appeared $warning_count times"
        cat "$TEMP_OUTPUT"
        exit 1
    else
        print_warning "Topic had $warning_count temporary publishing interruptions (tolerated)"
    fi
fi

# Parse the output
print_info "Parsing benchmark results..."
cat "$TEMP_OUTPUT"

# Extract metrics using grep and awk
AVERAGE_RATE=$(grep "average rate:" "$TEMP_OUTPUT" | awk '{print $3}' | head -1)
MIN_TIME=$(grep "min:" "$TEMP_OUTPUT" | awk '{print $2}' | sed 's/s$//' | head -1)
MAX_TIME=$(grep "max:" "$TEMP_OUTPUT" | awk '{print $4}' | sed 's/s$//' | head -1)
STD_DEV=$(grep "std dev:" "$TEMP_OUTPUT" | awk '{print $7}' | sed 's/s$//' | head -1)

# Validate that we got the metrics
if [ -z "$AVERAGE_RATE" ] || [ -z "$MIN_TIME" ] || [ -z "$MAX_TIME" ]; then
    print_error "Failed to parse benchmark metrics from output"
    print_info "Raw output:"
    cat "$TEMP_OUTPUT"
    exit 1
fi

# Calculate jitter (difference between max and min times)
JITTER=$(awk -v max="$MAX_TIME" -v min="$MIN_TIME" 'BEGIN {print max - min}')

# Display results
echo ""
print_info "=== BENCHMARK RESULTS ==="
echo "Topic: $ROS_BENCHMARK_TOPIC"
echo "Average Rate: $AVERAGE_RATE Hz"
echo "Min Time: ${MIN_TIME}s"
echo "Max Time: ${MAX_TIME}s"
echo "Jitter: ${JITTER}s"
echo "Std Dev: ${STD_DEV}s"

# Function to compare floating point numbers using awk
compare_float() {
    local val1=$1
    local op=$2
    local val2=$3
    awk -v v1="$val1" -v v2="$val2" -v op="$op" 'BEGIN {
        if (op == "<") exit !(v1 < v2)
        if (op == ">") exit !(v1 > v2)
        if (op == "<=") exit !(v1 <= v2)
        if (op == ">=") exit !(v1 >= v2)
        if (op == "==") exit !(v1 == v2)
        if (op == "!=") exit !(v1 != v2)
    }'
}

# Track if any checks failed
BENCHMARK_FAILED=0

echo ""
print_info "=== BENCHMARK VALIDATION ==="

# Check if average rate meets minimum requirement
if compare_float "$AVERAGE_RATE" "<" "$ROS_BENCHMARK_MIN_RATE"; then
    print_error "FAIL: Average rate ($AVERAGE_RATE Hz) is below minimum required rate ($ROS_BENCHMARK_MIN_RATE Hz)"
    BENCHMARK_FAILED=1
else
    print_info "PASS: Average rate ($AVERAGE_RATE Hz) meets minimum requirement ($ROS_BENCHMARK_MIN_RATE Hz)"
fi

# Check if jitter is within acceptable range
if compare_float "$JITTER" ">" "$ROS_BENCHMARK_MAX_JITTER"; then
    print_error "FAIL: Jitter ($JITTER s) exceeds maximum allowed jitter ($ROS_BENCHMARK_MAX_JITTER s)"
    BENCHMARK_FAILED=1
else
    print_info "PASS: Jitter ($JITTER s) is within acceptable range ($ROS_BENCHMARK_MAX_JITTER s)"
fi

# Check if standard deviation is within acceptable range
if compare_float "$STD_DEV" ">" "$ROS_BENCHMARK_MAX_STD"; then
    print_error "FAIL: Standard deviation ($STD_DEV s) exceeds maximum allowed ($ROS_BENCHMARK_MAX_STD s)"
    BENCHMARK_FAILED=1
else
    print_info "PASS: Standard deviation ($STD_DEV s) is within acceptable range ($ROS_BENCHMARK_MAX_STD s)"
fi

# Export results as environment variables for potential use by calling scripts
export BENCHMARK_AVERAGE_RATE="$AVERAGE_RATE"
export BENCHMARK_MIN_TIME="$MIN_TIME"
export BENCHMARK_MAX_TIME="$MAX_TIME"
export BENCHMARK_JITTER="$JITTER"
export BENCHMARK_STD_DEV="$STD_DEV"

# Final result
if [ $BENCHMARK_FAILED -eq 1 ]; then
    echo ""
    print_error "BENCHMARK FAILED - One or more performance criteria not met"
    exit 1
else
    echo ""
    print_info "BENCHMARK PASSED - All performance criteria met successfully!"
    exit 0
fi
