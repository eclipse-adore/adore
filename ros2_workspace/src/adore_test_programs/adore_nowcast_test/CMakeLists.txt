cmake_minimum_required(VERSION 3.8)
project(adore_nowcast_test VERSION 1.0.0 LANGUAGES CXX)

# C++20 strict mode
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

# Dependencies
find_package(adore_tridap REQUIRED)

set(adore_nowcast_test_SRCS
   adore_nowcast_test.cpp
)

add_executable(adore_nowcast_test ${adore_nowcast_test_SRCS})

# Include paths
target_include_directories(adore_nowcast_test
  PUBLIC ${adore_nowcast_INCLUDE_DIRS}
)

target_link_libraries(adore_nowcast_test
  PUBLIC
     adore_tridap::adore_tridap
)

install(TARGETS adore_nowcast_test
  EXPORT adore_nowcast_testTargets
  RUNTIME DESTINATION bin
)
