cmake_minimum_required(VERSION 3.22)

get_filename_component(CURRENT_DIR_NAME ${CMAKE_CURRENT_SOURCE_DIR} NAME)
set(PROJECT ${CURRENT_DIR_NAME})
project(${PROJECT})

set(CMAKE_EXPORT_COMPILE_COMMANDS ON CACHE INTERNAL "")
set(BUILD_DIRECTORY "${CMAKE_CURRENT_LIST_DIR}/build")
set(CMAKE_SHARE_DIRECTORY "${BUILD_DIRECTORY}/share")

set(PACKAGE_NAME "ADORe_${PROJECT}")
set(PACKAGE_VENDOR "DLR TS-KOS")
set(PACKAGE_DESCRIPTION "Assorted libraries for ADORe")
set(PACKAGE_MAINTAINER "DLR TS-KOS")
set(PACKAGE_MAINTAINER_EMAIL " opensource-ts@dlr.de")
set(CMAKE_BUILD_TYPE Release)
set(CMAKE_CXX_FLAGS "-std=c++17 -Wall -Wextra -O3")

set(CMAKE_BUILD_TYPE Release)
set(CMAKE_CXX_FLAGS "-std=c++17 -Wall -Wextra -O3")

message(STATUS "============================")
message(STATUS "Project: ${PROJECT}")
message(STATUS "Build Directory: ${BUILD_DIRECTORY}")
message(STATUS "Share Directory: ${CMAKE_SHARE_DIRECTORY}")
message(STATUS "Package Name: ${PACKAGE_NAME}")
message(STATUS "Package Vendor: ${PACKAGE_VENDOR}")
message(STATUS "Package Description: ${PACKAGE_DESCRIPTION}")
message(STATUS "Package Maintainer: ${PACKAGE_MAINTAINER}")
message(STATUS "Package Maintainer Email: ${PACKAGE_MAINTAINER_EMAIL}")
message(STATUS "============================")


include(cmake/packaging.cmake)
include(cmake/util_functions.cmake)
include(cmake/package_functions.cmake)
include(cmake/target_functions.cmake)
include(cmake/debugging_functions.cmake)
include(cmake/library_functions.cmake)


find_all_requirements("${CMAKE_SOURCE_DIR}")

if (PRINT_LIBRARY_INFO)
    find_all_libraries("${CMAKE_SHARE_DIRECTORY}")
    print_cmake_libraries("${CMAKE_SHARE_DIRECTORY}")
    exit()
endif()

if (PRINT_CMAKE_VARIABLES)
    generate_library_targets(${CMAKE_CURRENT_SOURCE_DIR}/lib)
    generate_executable_targets(${CMAKE_CURRENT_SOURCE_DIR}/lib)
    print_cmake_variables()
    exit()
endif()

if (PRINT_PACKAGE_INFO)
    generate_library_targets(${CMAKE_CURRENT_SOURCE_DIR}/lib)
    generate_executable_targets(${CMAKE_CURRENT_SOURCE_DIR}/lib)
    print_cmake_packages()
    exit()
endif()

if (PRINT_TARGET_INFO)
    generate_library_targets(${CMAKE_CURRENT_SOURCE_DIR}/lib)
    generate_executable_targets(${CMAKE_CURRENT_SOURCE_DIR}/lib)
    print_cmake_targets()
    exit()
endif()

generate_library_targets(${CMAKE_CURRENT_SOURCE_DIR}/lib)
generate_executable_targets(${CMAKE_CURRENT_SOURCE_DIR}/lib)
