# ROS 2 Workspace Makefile

This Makefile automates building, cleaning, testing, and running ROS 2 packages 
in a workspace, with intelligent build settings based on available system RAM.

## Overview

- **Adaptive parallelism**: Uses all CPU cores minus one (or two in release mode) if ≥ 8 GB RAM is detected, otherwise falls back to sequential builds.
- **Helper targets** for building, cleaning, testing, running scenarios, and managing ROS 2 processes.
- **Colcon-based builds** with both debug and release configurations.
- **Integration with external libraries** and scenarios.

---

## Usage

```bash
make <target>
```

Run `make help` to see available targets and descriptions.

---

## Targets

| Target                    | Description |
|---------------------------|-------------|
| `help`                    | Show usage information and all available targets. |
| `build`                   | Build all ROS 2 packages using adaptive parallelism. |
| `build_release`           | Build all ROS 2 packages in **Release** mode with adaptive parallelism. |
| `build_single_core`       | Force a single-threaded build regardless of RAM. |
| `build_user_libraries`    | Build user libraries from `../libraries` directory. |
| `build_libraries_and_nodes` | Build both user libraries and ROS 2 packages in release mode. |
| `clean`                   | Remove `build/`, `log/`, and `install/` directories. |
| `clean_build`             | Clean and rebuild all ROS 2 packages. |
| `test`                    | Run tests on all packages (excluding linters). |
| `ccache_stats`            | Display CCache statistics. |
| `launch`                  | Interactively select and launch a scenario from `../adore_scenarios`. |
| `integration_tests`       | Run pytest inside `../adore_scenarios`. |
| `force_kill_ros2`         | Forcefully kill all ROS 2 related processes. |

