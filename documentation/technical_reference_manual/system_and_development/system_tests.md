# ADORe System Tests

ADORe includes shell-based system tests validate high-level features including 
scenario execution, model checking, and API functionality. These tests run 
automatically as part of the GitHub CI workflow.

## Prerequisites

- GNU Make and docker are installed
- ADORe repository cloned locally
- ADORe is built
- ADORe CLI stopped (if running)

## Running Tests

From the ADORe repository root:

```bash
# Stop ADORe CLI if running
make stop

# Execute all system tests
make test
```

## Writing System Tests

Add new test functions to `.tests` in the repository root.

### Test Function Naming Convention
All system tests have the following function name convention:
```bash
<index>_<test_name>_test
```

- **Index**: Controls execution order (tests run alphabetically)
- **Name**: Descriptive test identifier
- **Suffix**: Must end with `_test` for automatic execution

### Environment

- `LOG_DIRECTORY`: Available environment variable for log output
- Log files: Write to `${LOG_DIRECTORY}/<test_name>.log`
- Return codes: `0` for success, `1` for failure

### Test Template

```bash
XX_test_name_test() {
    local action=test_action
    local name="Test Name Here"
    local description="This test runs 'make test_command' and validates the output."
    local status=""
    local message=""
    local test_log_file="${LOG_DIRECTORY}/test_command.log"
    
    printf "\n"
    printf "  Test: %s\n" "${name}"
    printf "    Description: %s\n" "${description}"
    printf "      This test runs [detailed description of what the test validates]. \n"
    printf "    Starting make test_command...\n"
    
    if ! make test_command >"$test_log_file" 2>&1; then
        status=$(bold $(red "FAILED"))
        message="        Make test_command command failed. See log: ${test_log_file}"
        cat "${test_log_file}"
        printf "    Message:\n%s\n" "$message"
        printf "    %-77s %s\n" "Status:" "${status}"
        exit 1
    fi
    
    status=$(bold $(green "PASSED"))
    message="        Make test_command succeeded. Tail of log shown below:"
    printf "    Message:\n%s\n" "$message"
    tail -15 "${test_log_file}"
    printf "    %-77s %s\n" "Status:" "${status}"
    printf "    See the test_command log for full details: %s\n" "$test_log_file"
    exit 0
}
```

### Best Practices

- Keep test functions focused on a single feature or scenario
- Provide clear, descriptive test names and descriptions
- Log all output for debugging purposes
- Display meaningful error messages on failure
- Show partial log output (tail) on success for quick verification
