cmake_minimum_required(VERSION 3.10)
project(adore_scenarios)

# Dependencies
find_package(ament_cmake REQUIRED)
find_package(rclpy REQUIRED)
find_package(launch_testing_ament_cmake REQUIRED)
find_package(adore_ros2_msgs REQUIRED)
# Install Python modules
install(DIRECTORY
  simulation_scenarios
  scenario_helpers
  DESTINATION share/${PROJECT_NAME}/
)

# ----------------------
# Testing
# ----------------------
if(BUILD_TESTING)
  # Add launch test(s)
  add_launch_test(
    integration_tests/sad_test.py
    TARGET sad_test
  )

endif()

ament_package()