````markdown
# System & end-to-end tests

This document describes the **system / end-to-end testing layer** in this repository and how to extend it with new tests.

The audience is developers who are already comfortable with unit / integration tests inside individual ROS 2 packages and want to test the **whole system**: API, long-running processes, simulations, GUI, external tools, etc.

---

## What system tests are for

System tests here are:

- **Black-box**: they interact with the running ADORe stack via public interfaces  
  (HTTP API, CLI tools, GUI/X11, files on disk…).
- **End-to-end**: they aim to cover the full path from an external stimulus to the observable behaviour of the system.
- **Slow(er) but high value**: they are allowed to take longer than unit tests, but should still be stable, deterministic and CI-friendly.

Typical things to validate:

- “Is the API up and responding with valid JSON?”
- “Can we start a scenario and get sensible model-checking results?”
- “Can GUI tools inside the container talk to the host X server?”
- “Do our compliance / scanning tools pass with the current tree?”

---

## Where system tests live

System tests are implemented as shell scripts under:

```text
tools/system_tests/
  run_system_tests.sh       # test runner / harness
  test_helpers.sh           # shared helpers (logging, colors, API readiness, etc.)
  NN_some_feature_test.sh   # individual test scripts (you add more here)
  ...
````

### Entry point

From the repo root, the canonical way to run system tests is:

```bash
just test_system
```

`Justfile` defines:

```make
# Run system tests
test_system:
    ./tools/system_tests/run_system_tests.sh
```

So you can also invoke the runner directly:

```bash
./tools/system_tests/run_system_tests.sh
```

The runner script is responsible for:

* Starting the system under test (e.g. API server) before any tests run.
* Discovering test functions and executing them sequentially.
* Setting an appropriate process exit code based on pass/fail.
* Stopping the system under test again at the end.

---

## Test harness behaviour

The harness (`run_system_tests.sh`) behaves roughly like this:

1. **Start the system under test**

   It uses `just` commands (for example `just api_start` / `just api_stop`) to bring up and tear down the environment the tests rely on.

2. **Load helpers and test scripts**

   It sources:

   * `test_helpers.sh` – common helpers and configuration.
   * All `*_test.sh` files in the same directory – where each file can define one or more test functions.

3. **Discover test functions**

   It collects all shell functions with a name ending in `_test`, sorts them, and treats each as an individual test case.

   That means:

   * You don’t need to register a new test anywhere.
   * As long as the function name ends in `_test` and the file is `*_test.sh`, it will be picked up.

4. **Execute tests**

   Each test function is executed in a subshell. The harness:

   * Prints which test is running.
   * Consider the test **passed** if the function returns exit code `0`.
   * Consider the test **failed** if the function returns a non-zero code.
   * Continues to the next test even if one fails.

   At the end it exits with:

   * `0` if all tests passed.
   * `1` if any test failed.

5. **Stop the system under test**

   After all tests, the harness calls the appropriate `just` command to stop the system (e.g. shutting down the API process).

---

## Shared helpers

`test_helpers.sh` provides shared functionality for all system tests, for example:

* Simple formatting helpers (bold / coloured output).
* Common configuration variables (e.g. log directory, timeouts).
* Routines to wait for the system or API to be “ready” (polling a status endpoint until it responds, with a timeout).

When writing new tests:

* Always source `test_helpers.sh` via the runner (you don’t need to do this manually; the runner already does).
* Prefer using the existing helpers rather than re-implementing things like “wait for API to be ready”.
* If you need reusable logic for multiple system tests, extend `test_helpers.sh` rather than copying functions between `*_test.sh` files.

---

## Naming and structure conventions

### File naming

System test scripts follow this pattern:

```text
tools/system_tests/NN_descriptive_name_test.sh
```

Guidelines:

* `NN_` is a **two-digit prefix** (e.g. `01_`, `02_`, …) that controls ordering.
  Use it if you care about approximate execution order (e.g. smoke tests first).
* `descriptive_name` should describe the theme of the script (“api_health”, “scenario_simulation”, “x11_integration”, etc.).
* `_test.sh` suffix marks the file as a test script.

You can have more than one test function in a single file if it makes sense to group related checks.

### Function naming

A function is treated as a test if its name ends in `_test`, e.g.:

```bash
smoke_test()
scenario_model_checking_test()
gui_integration_test()
```

Guidelines:

* Use a unique, descriptive name — it will appear in the harness output.
* Prefer one “main” test function per file unless you have a clear grouping.
* Helper functions **should not** end in `_test` (so they aren’t auto-executed).

### Test function contract

Each test function:

* **Takes no arguments.**
* Performs whatever actions it needs (HTTP calls, CLI invocations, etc.).
* Prints human-readable output describing what it’s doing and what it found.
* Returns:

  * `0` on success.
  * A non-zero exit code on failure.

The harness uses this exit code to decide whether the test passed or failed.

---

## What a new system test typically looks like

Here is a recommended skeleton for a new test function:

```bash
my_new_feature_test() {
  local name="My new feature behaves end-to-end"
  local description="Short description of what this system test validates."
  local status=""
  local message=""

  printf "\n"
  printf "  Test: %s\n" "${name}"
  printf "    Description: %s\n" "${description}\n"

  # Optional: wait for API/system readiness using a helper
  # if ! wait_for_api_ready; then
  #   printf "    Status: %s - system not ready\n" "$(bold "$(red "FAILED")")"
  #   return 1
  # fi

  # --- Arrange / Act / Assert section ---------------------------------
  # 1. Arrange: put the system into the desired initial state
  # 2. Act: call the API / CLI / GUI action you want to test
  # 3. Assert: inspect responses, logs, or side effects

  # Example pseudo-check:
  # if ! curl ...; then
  #   message="Some failure description"
  #   status="$(bold "$(red "FAILED")")"
  #   printf "    Message:\n        %s\n" "${message}"
  #   printf "    %-77s %s\n" "Status:" "${status}"
  #   return 1
  # fi

  message="Short success summary (what we actually validated)."
  status="$(bold "$(green "PASSED")")"

  printf "    Message:\n        %s\n" "${message}"
  printf "    %-77s %s\n" "Status:" "${status}"

  return 0
}
```

Feel free to adapt the formatting, as long as:

* The function’s exit code correctly represents pass/fail.
* Output is understandable by a human reading CI logs.

---

## Logging and diagnostics

System tests should be **debuggable** when they fail. Some general recommendations:

* Write richer machine-readable logs (JSON, structured text) into a shared log directory; keep console output concise.
* Include enough context in the log file names (e.g. the domain of the check).
* When a test fails, print the tail or a short summary of the relevant log(s) to stdout so CI logs contain a hint without having to dig into artefacts.

The helpers script defines where logs are stored by default and may allow overriding the log directory via an environment variable (e.g. for CI vs local runs). Check `test_helpers.sh` for the exact variable names and behaviour.

---

## What to test at the system level

Some ideas for system-level checks you might want to add:

* **API behaviour**

  * Smoke tests for key endpoints (status, scenario control, configuration).
  * Schema / field sanity checks (e.g. unique IDs, expected ranges).
  * Error handling for invalid input.

* **Scenario execution**

  * Start a scenario, let it run for some time, check that:

    * Expected outputs (reports, artefacts, logs) are generated.
    * No obvious error states are present in responses.
  * Round-trip across multiple API calls (start, query progress, stop, retrieve results).

* **Integration with external tools**

  * Running internal scanning / analysis tools and checking they succeed.
  * Verifying required OS-level functionality (e.g. presence of system utilities, access to required resources).

* **GUI / X11 integration**

  * Launch a minimal GUI app inside the dev/CI environment and verify it can talk to the host X server.
  * Confirm a window appears in the X11 tree.

* **Non-functional behaviour**

  * Very coarse performance sanity checks (e.g. “scenario finishes within N seconds on CI hardware”).
  * Resource usage thresholds (if those can be tested reliably).

When deciding whether something belongs in a system test versus a unit / integration test, ask:

> “Does this require the **whole stack** to be running and realistic user workflows to be exercised?”

If the answer is yes, it probably belongs here.

---

## Design guidelines for new system tests

* **Idempotent and repeatable**
  Tests should be safe to run multiple times in a row, and in any order. Avoid leaving behind state that breaks subsequent runs.

* **Isolated**
  Avoid relying on side effects from previous tests; set up the state you need in each test.

* **Deterministic**
  Avoid flakiness (e.g. random sleep durations with no checks, reliance on external services that may be down, unbounded timeouts).

* **Configurable**
  Use / extend environment variables for things like:

  * API base URL
  * timeouts
  * log locations
    so that CI and local runs can tweak behaviour without changing code.

* **Fast enough for CI**
  Individual system tests can be slower than unit tests, but should still complete in a reasonable time. If something needs several minutes, consider splitting it or enabling it only in certain pipelines.

* **Use shared helpers**
  If you find yourself copying the same snippets (curl patterns, JSON extraction, polling loops), move them into `test_helpers.sh`.

---

## Adding a new system test: checklist

1. **Create a new file** under `tools/system_tests/` with the pattern:

   ```text
   NN_my_feature_test.sh
   ```

2. **Add one or more functions** in that file whose names end in `_test`.

3. **Use or extend shared helpers** in `test_helpers.sh` instead of duplicating logic.

4. **Make the function self-contained**:

   * Arrange, act, assert.
   * Print a clear message on success and on failure.
   * Return `0` for success, non-zero for failure.

5. **Run locally**:

   ```bash
   just test_system
   ```