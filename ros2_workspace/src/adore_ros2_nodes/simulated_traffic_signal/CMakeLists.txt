cmake_minimum_required(VERSION 3.21)
project(simulated_traffic_signal VERSION 0.1.0 LANGUAGES CXX)

# C++20 strict mode
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# Compile commands for IDEs
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

# Optimization and warning flags
if(CMAKE_BUILD_TYPE STREQUAL "Release")
  add_compile_options(-O3)
endif()

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# Dependencies
find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(rclcpp_components REQUIRED)
find_package(caches REQUIRED PATHS ${CMAKE_INSTALL_PREFIX}/../caches/lib/cmake/caches)
find_package(adore_map REQUIRED)
find_package(adore_math REQUIRED)
find_package(adore_ros2_msgs REQUIRED)

find_package(std_msgs REQUIRED)
find_package(tf2 REQUIRED)
find_package(tf2_ros REQUIRED)

# Executable
add_executable(${PROJECT_NAME}
  src/simulated_traffic_signal.cpp
  src/main.cpp
)

target_include_directories(${PROJECT_NAME}
  PRIVATE
    $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
    $<INSTALL_INTERFACE:include>
)

ament_target_dependencies(${PROJECT_NAME}
  rclcpp
  rclcpp_components
  adore_map
  adore_math
  adore_ros2_msgs
  std_msgs
  tf2
  tf2_ros
)

install(TARGETS ${PROJECT_NAME}
  DESTINATION lib/${PROJECT_NAME}
)

# Component Library
add_library(${PROJECT_NAME}_component SHARED src/simulated_traffic_signal.cpp)

target_include_directories(${PROJECT_NAME}_component
  PRIVATE
    $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
    $<INSTALL_INTERFACE:include>
)

ament_target_dependencies(${PROJECT_NAME}_component
  rclcpp
  rclcpp_components
  adore_math
  adore_ros2_msgs
  adore_map
  std_msgs
  tf2
  tf2_ros
)

rclcpp_components_register_node(
  ${PROJECT_NAME}_component
  PLUGIN "adore::simulated_traffic_signal::SimulatedTrafficSignalNode"
  EXECUTABLE simulatedtrafficsignalnode
)

install(TARGETS ${PROJECT_NAME}_component
  ARCHIVE DESTINATION lib
  LIBRARY DESTINATION lib
  RUNTIME DESTINATION bin
)

ament_package()
