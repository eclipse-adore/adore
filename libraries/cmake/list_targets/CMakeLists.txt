cmake_minimum_required(VERSION 3.27)

get_filename_component(CURRENT_DIR_NAME ${CMAKE_CURRENT_SOURCE_DIR} NAME)
set(PROJECT ${CURRENT_DIR_NAME})
project(${PROJECT})

include(debugging_functions.cmake)
include(library_functions.cmake)


#print_targets()
#print_cmake_variables()

