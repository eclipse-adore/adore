
set(ADORE_LIBRARIES_DIRECTORY "${CMAKE_CURRENT_LIST_DIR}")

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)


include("${ADORE_LIBRARIES_DIRECTORY}/cmake/util_functions.cmake")
include("${ADORE_LIBRARIES_DIRECTORY}/cmake/debugging_functions.cmake")
include("${ADORE_LIBRARIES_DIRECTORY}/cmake/package_functions.cmake")
include("${ADORE_LIBRARIES_DIRECTORY}/cmake/library_functions.cmake")
include("${ADORE_LIBRARIES_DIRECTORY}/cmake/target_functions.cmake")
message("  ADORE_LIBRARIES_DIRECTORY: ${ADORE_LIBRARIES_DIRECTORY}")
find_all_requirements("${ADORE_LIBRARIES_DIRECTORY}/lib")
find_all_libraries("${ADORE_LIBRARIES_DIRECTORY}/build/share")
#print_cmake_libraries(${ADORE_LIBRARIES_DIRECTORY}/build/share)
generate_library_targets(${CMAKE_CURRENT_SOURCE_DIR}/lib)
#generate_executable_targets(${CMAKE_CURRENT_SOURCE_DIR}/lib)
