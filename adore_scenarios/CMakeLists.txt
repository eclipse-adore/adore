cmake_minimum_required(VERSION 3.10)
project(adore_scenarios)

# Dependencies
find_package(ament_cmake REQUIRED)
find_package(rclpy REQUIRED)
find_package(launch_testing_ament_cmake REQUIRED)
find_package(adore_ros2_msgs REQUIRED)
# Install Python modules
install(DIRECTORY
  adore_simulation_scenarios
  scenario_helpers
  DESTINATION share/${PROJECT_NAME}/
)

# Install launch files
install(
  DIRECTORY
    scenario_helpers/
  DESTINATION
    share/${PROJECT_NAME}/
)

install(
  DIRECTORY
    adore_simulation_scenarios/
  DESTINATION
    share/${PROJECT_NAME}/
)

# Install integration test files
install(
  DIRECTORY
    integration_tests
  DESTINATION
    share/${PROJECT_NAME}/
)


install(
  DIRECTORY
    assets/
  DESTINATION
    share/${PROJECT_NAME}/
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
    # Add launch test(s)
  # add_launch_test(
  #   integration_tests/mad_test.py
  #   TARGET mad_test
  # )
endif()

ament_package()