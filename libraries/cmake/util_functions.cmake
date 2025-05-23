
message("util_functions.cmake loaded")

function(cmakeignore PATH IGNORE_FILE RETURN_VALUE)

    string(REPLACE "${CMAKE_SOURCE_DIR}/" "" relative_path ${PATH})
    execute_process(
        COMMAND bash -c "cd ${CMAKE_SOURCE_DIR} && python3 cmake/ignore/ignore.py \"${relative_path}\" \"${IGNORE_FILE}\""
        RESULT_VARIABLE CMD_RESULT
    )

    if(CMD_RESULT EQUAL 1)
        #message("  TRUE")
        set(${RETURN_VALUE} TRUE PARENT_SCOPE)
        set(${RETURN_VALUE} FALSE)
    else()
        #message("  FALSE")
        set(${RETURN_VALUE} FALSE PARENT_SCOPE)
        set(${RETURN_VALUE} FALSE)
    endif()

    #message("  cmakeignore: ${relative_path} IGNORE_FILE: ${IGNORE_FILE} ignored: ${RETURN_VALUE}")
endfunction()


macro(find_all_requirements base_directory)
    file(GLOB_RECURSE requirement_files "${base_directory}/**/requirements.cmake")

    #message("")
    foreach(requirement_file ${requirement_files})
        #message("    Including cmake requirements file: ${requirement_file}")
        include(${requirement_file})
    endforeach()
endmacro()


