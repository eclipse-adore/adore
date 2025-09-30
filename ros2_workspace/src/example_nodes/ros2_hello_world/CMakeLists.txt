cmake_minimum_required(VERSION 3.8)

get_filename_component(CURRENT_DIR_NAME ${CMAKE_CURRENT_SOURCE_DIR} NAME)
string(TOLOWER ${CURRENT_DIR_NAME} PROJECT)
project(${PROJECT})

include($ENV{SOURCE_DIRECTORY}/libraries/adore_libraries.cmake)

include(requirements.cmake)

add_executable(${PROJECT} src/${PROJECT}.cpp)

target_include_directories(${PROJECT} PRIVATE
  $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
  $<INSTALL_INTERFACE:include>
)


# Auto-link all ADORe user libraries
add_all_target_include_directories(${PROJECT})
add_all_target_link_libraries(${PROJECT})

file(GLOB_RECURSE TEST_SOURCES test/*.cpp)
if(TEST_SOURCES)
    ament_add_gtest(${PROJECT}_test ${TEST_SOURCES})
    if(TARGET ${PROJECT}_test)
        ament_target_dependencies(${PROJECT}_test rclcpp std_msgs)
    endif()
endif()

#ament_add_gtest(${PROJECT}_test test/${PROJECT}_test.cpp)
#if(TARGET ${PROJECT}_test)
#    ament_target_dependencies(${PROJECT}_test rclcpp std_msgs)
#endif()


install(TARGETS
    ${PROJECT}
  DESTINATION lib/${PROJECT}
)

ament_package()
