cmake_minimum_required(VERSION 3.8)
project(adore_weather_forecast_downloader_test VERSION 1.0.0 LANGUAGES CXX)
# C++20 strict mode
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)
# Dependencies
find_package(adore_tridap REQUIRED)
set(adore_weather_forecast_downloader_test_SRCS
   adore_weather_forecast_downloader_test.cpp
)
add_executable(adore_weather_forecast_downloader_test ${adore_weather_forecast_downloader_test_SRCS})
# Include paths
target_include_directories(adore_weather_forecast_downloader_test
  PUBLIC ${adore_tridap_INCLUDE_DIRS}
)
target_link_libraries(adore_weather_forecast_downloader_test
  PUBLIC
     adore_tridap::adore_tridap
)
install(TARGETS adore_weather_forecast_downloader_test
  EXPORT adore_weather_forecast_downloader_testTargets
  RUNTIME DESTINATION bin
)