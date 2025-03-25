
message("library_functions.cmake loaded")

function(get_libraries CMAKE_SHARE_DIRECTORY LIBRARIES)
    #message("    CMAKE_SHARE_DIRECTORY: ${CMAKE_SHARE_DIRECTORY}")

    if(EXISTS "${CMAKE_SHARE_DIRECTORY}" AND IS_DIRECTORY "${CMAKE_SHARE_DIRECTORY}")

        #message(STATUS "    CMAKE_SHARE_DIRECTORY: ${CMAKE_SHARE_DIRECTORY}")

        execute_process(
            COMMAND bash -c "grep -rn 'add_library' '${CMAKE_SHARE_DIRECTORY}' | grep -o -P '(?<=\\().*?(?=\\))' | cut -d ':' -f1 | sort | uniq"
            OUTPUT_VARIABLE LIBRARIES_OUTPUT
            RESULT_VARIABLE COMMAND_RESULT
            OUTPUT_STRIP_TRAILING_WHITESPACE
        )

        if(NOT COMMAND_RESULT EQUAL 0)
            message(FATAL_ERROR "Error running the command to get libraries.")
        endif()

        string(REPLACE "\n" ";" LIBRARIES_LIST "${LIBRARIES_OUTPUT}")

        set(LIBRARIES ${LIBRARIES_LIST} PARENT_SCOPE)
    else()
        #message(FATAL_ERROR "ERROR: The supplied CMAKE_SHARE_DIRECTORY: ${CMAKE_SHARE_DIRECTORY} does not exits. Did you build the libraries? Build the libraries and try again.")
    endif()
endfunction()

macro(find_all_libraries CMAKE_SHARE_DIRECTORY)
    _find_all_libraries(${CMAKE_SHARE_DIRECTORY})
    _find_all_libraries(${CMAKE_SHARE_DIRECTORY})
endmacro()

macro(_find_all_libraries CMAKE_SHARE_DIRECTORY)
    list(APPEND CMAKE_PREFIX_PATH "${CMAKE_SHARE_DIRECTORY}")
    #message("  CMAKE_PREFIX_PATH: ${CMAKE_PREFIX_PATH}")
    get_libraries(${CMAKE_SHARE_DIRECTORY} LIBRARIES)
    #message("  CMake Libraries: ${LIBRARIES}")
    #message("  CMake Libraries:")
    foreach(library ${LIBRARIES})
        find_package(${library} QUIET CONFIG)
        set(${library}_TARGETS "${library}::${library}")
        set(${library}_LIBRARIES "${library}::${library}")
        set(${library}_headers_DIR "${CMAKE_CURRENT_SOURCE_DIR}/build/lib/${library}/include")
        set(${library}_INCLUDE_DIRS "${CMAKE_CURRENT_SOURCE_DIR}/build/lib/${library}/include")
    endforeach()
endmacro()
