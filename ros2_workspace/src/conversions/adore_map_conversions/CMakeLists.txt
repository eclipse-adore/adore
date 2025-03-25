cmake_minimum_required(VERSION 3.8)

# Use the directory name as the project name
get_filename_component(CURRENT_DIR_NAME ${CMAKE_CURRENT_SOURCE_DIR} NAME)
string(TOLOWER ${CURRENT_DIR_NAME} PROJECT)
project(${PROJECT})

# Include common ROS2 and package dependencies
include($ENV{SOURCE_DIRECTORY}/libraries/adore_libraries.cmake)
include(requirements.cmake)

# Ensure the Release build uses -O3 for optimization
if(CMAKE_BUILD_TYPE STREQUAL "Release")
  add_compile_options(-O3)
endif()

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# Define a library 
add_library(${PROJECT} STATIC
    src/${PROJECT}.cpp
)

# Include directories
target_include_directories(${PROJECT} PUBLIC
  $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
  $<INSTALL_INTERFACE:include>
)

# Link dependencies
add_all_target_include_directories(${PROJECT})
add_all_target_link_libraries(${PROJECT})

# Ensure this library can be found by other packages
ament_export_targets(export_${PROJECT} HAS_LIBRARY_TARGET)

# Install the library and headers
install(
  TARGETS ${PROJECT}
  EXPORT export_${PROJECT}
  LIBRARY DESTINATION lib
  ARCHIVE DESTINATION lib
  RUNTIME DESTINATION bin
  INCLUDES DESTINATION include
)

install(
  DIRECTORY include/
  DESTINATION include
)

ament_package()
