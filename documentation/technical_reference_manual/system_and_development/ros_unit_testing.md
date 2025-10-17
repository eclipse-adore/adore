# ROS Unit Testing

As with ROS, ADORe supports unit testing with colcon.

## Executing All ROS Unit Tests

All ROS unit tests can be run with the following:

```bash
# 1. Start and attach to the ADORe CLI
make cli

# 2. Navigate to the ros2_workspace and run make test
cd ros2_workspace
make test

# Optionally, you can invoke colcon directly
colcon test --pytest-args "-m 'not linter'" --event-handlers console_direct+
```

## C++ Template Project

In `ros2_workspace/src/example_nodes/ros2_hello_world`, ADORe includes a complete template C++ node example that includes unit tests. This project can be used as a basis/template for another node to include unit tests.

This project also includes a generic Makefile that includes targets: `make build`, `make test` and `make run`.

To run the tests for the `ros2_hello_world` program use the following:

```bash
# 1. Start and attach to the ADORe CLI
make cli

# 2. Navigate to the ros2_hello_world directory and run make test
cd ros2_workspace/src/example_nodes/ros2_hello_world
make test

# Optionally, you can invoke colcon directly
cd ros2_workspace && colcon test --packages-select ros2_hello_world --event-handlers console_direct+
```

Example output:
```
make cli
cd ros2_workspace/src/example_nodes/ros2_hello_world
make test
...
1/1 Test #1: ros2_hello_world_test ............   Passed    0.07 sec

100% tests passed, 0 tests failed out of 1

Label Time Summary:
gtest    =   0.07 sec*proc (1 test)

Total Test time (real) =   0.07 sec
Finished <<< ros2_hello_world [0.11s]
```

## Python Template Project

In `ros2_workspace/src/example_nodes/ros2_python_hello_world`, ADORe provides a complete template Python node example with comprehensive unit tests. This project demonstrates Python-specific testing patterns and can serve as a foundation for developing Python-based ROS2 nodes with proper test coverage.

The Python template includes:
- Unit tests using `pytest` framework
- Mock testing for ROS2 interfaces
- Coverage reporting capabilities
- A generic Makefile with `make build`, `make test`, and `make run` targets

### Running Python Node Tests

To run the tests for the `ros2_python_hello_world` program:

```bash
# 1. Start and attach to the ADORe CLI
make cli

# 2. Navigate to the ros2_python_hello_world directory and run make test
cd ros2_workspace/src/example_nodes/ros2_python_hello_world
make test

# Optionally, you can invoke colcon directly
cd ros2_workspace && colcon test --packages-select ros2_python_hello_world --event-handlers console_direct+

# For verbose pytest output with coverage
cd ros2_workspace && colcon test --packages-select ros2_python_hello_world --pytest-args "-v --cov=ros2_python_hello_world" --event-handlers console_direct+
```

Example output:
```
make cli
cd ros2_workspace/src/example_nodes/ros2_python_hello_world
make test
...
============================= test session starts ==============================
platform linux -- Python 3.10.12, pytest-7.4.0
collected 3 items

test_hello_world_node.py::test_node_creation PASSED                     [ 33%]
test_hello_world_node.py::test_timer_callback PASSED                    [ 66%]
test_hello_world_node.py::test_message_publishing PASSED                [100%]

============================== 3 passed in 0.42s ===============================
Finished <<< ros2_python_hello_world [0.58s]
```

### Python Testing Best Practices

The Python template demonstrates several testing patterns specific to Python ROS2 development:

- **Fixture-based setup**: Uses pytest fixtures for node initialization and cleanup
- **Mocking ROS2 interfaces**: Demonstrates how to mock publishers, subscribers, and services
- **Async testing**: Includes examples for testing asynchronous ROS2 callbacks
- **Parameter testing**: Shows how to test node parameters and dynamic reconfiguration

### Coverage Reports

Generate detailed coverage reports for Python nodes:

```bash
cd ros2_workspace
colcon test --packages-select ros2_python_hello_world --pytest-args "--cov=ros2_python_hello_world --cov-report=html" --event-handlers console_direct+
# Coverage report will be available in ros2_workspace/build/ros2_python_hello_world/htmlcov/index.html
```
