message("util_functions.cmake loaded")

function(cmakeignore PATH IGNORE_FILE RETURN_VALUE)
    set(ignore_script "${CMAKE_CURRENT_LIST_DIR}/cmake/ignore/ignore.py")
    
    if(NOT EXISTS ${ignore_script})
        message(WARNING "ignore.py not found at: ${ignore_script}")
        set(${RETURN_VALUE} FALSE PARENT_SCOPE)
        return()
    endif()

    string(REPLACE "${CMAKE_SOURCE_DIR}/" "" relative_path ${PATH})
    execute_process(
        COMMAND python3 ${ignore_script} "${relative_path}" "${IGNORE_FILE}"
        WORKING_DIRECTORY ${CMAKE_SOURCE_DIR}
        RESULT_VARIABLE CMD_RESULT
    )

    if(CMD_RESULT EQUAL 1)
        set(${RETURN_VALUE} TRUE PARENT_SCOPE)
    else()
        set(${RETURN_VALUE} FALSE PARENT_SCOPE)
    endif()
endfunction()

macro(find_all_requirements base_directory)
    file(GLOB_RECURSE requirement_files "${base_directory}/**/requirements.cmake")

    foreach(requirement_file ${requirement_files})
        include(${requirement_file})
    endforeach()
endmacro()
