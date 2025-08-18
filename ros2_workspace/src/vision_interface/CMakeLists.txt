cmake_minimum_required(VERSION 3.21)

get_filename_component(CURRENT_DIR_NAME ${CMAKE_CURRENT_SOURCE_DIR} NAME)
string(TOLOWER ${CURRENT_DIR_NAME} PROJECT)
project(${PROJECT})

include($ENV{SOURCE_DIRECTORY}/libraries/adore_libraries.cmake)

include(requirements.cmake)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON CACHE INTERNAL "")
# Ensure the Release build uses -O3 for optimization
if(CMAKE_BUILD_TYPE STREQUAL "Release")
  add_compile_options(-O3)
endif()


add_executable(${PROJECT}  src/vision_interface_node.cpp)


target_include_directories(${PROJECT} PRIVATE
  $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
  $<INSTALL_INTERFACE:include>
)


add_all_target_include_directories(${PROJECT})
add_all_target_link_libraries(${PROJECT})



install(TARGETS
    ${PROJECT}
  DESTINATION lib/${PROJECT}
)

ament_package()

