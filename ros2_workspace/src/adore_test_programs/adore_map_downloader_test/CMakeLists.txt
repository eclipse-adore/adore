cmake_minimum_required(VERSION 3.8)
project(adore_map_downloader_test VERSION 1.0.0 LANGUAGES CXX)

# C++20 strict mode
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

# Dependencies
find_package(adore_map REQUIRED)
find_package(adore_tridap REQUIRED)

set(basic_map_loading_from_wfs_test_SRCS
   basic_map_loading_from_wfs_test.cpp
)

add_executable(basic_map_loading_from_wfs_test ${basic_map_loading_from_wfs_test_SRCS})

# Include paths
target_include_directories(basic_map_loading_from_wfs_test
  PUBLIC ${adore_map_INCLUDE_DIRS}
  PUBLIC ${adore_tridap_INCLUDE_DIRS}
)

target_link_libraries(basic_map_loading_from_wfs_test
  PUBLIC
     adore_map::adore_map
     adore_tridap::adore_tridap
)

install(TARGETS basic_map_loading_from_wfs_test
  EXPORT basic_map_loading_from_wfs_testTargets
  RUNTIME DESTINATION bin
)
