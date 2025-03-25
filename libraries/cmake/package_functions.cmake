
message("package_functions.cmake loaded")

function(index_of set item index)
    set(return_value -1)
    foreach(element ${set})
        math(EXPR return_value "${return_value} + 1")
        #message("element: ${element} item: ${item}")
        if(element STREQUAL ${item})
            break()
        endif()
    endforeach()
    set(${index} ${return_value} PARENT_SCOPE)
endfunction()

function(count input_list target_string package_count)
    set(return_value 0)
    foreach(item ${input_list})
        string(TOLOWER ${item} string1_lower)
        string(TOLOWER ${target_string} string2_lower)

        if(string1_lower STREQUAL string2_lower)
            math(EXPR return_value "${return_value} + 1")
            #message(" item:${item}  target_string: ${target_string} count: ${return_value}")
        endif()
    endforeach()
    set(${package_count} ${return_value} PARENT_SCOPE)
endfunction()

function(get_cmake_packages PACKAGES)
    get_cmake_property(variables VARIABLES)

    foreach(variable ${variables})
        if(variable MATCHES "_found$" OR variable MATCHES "_FOUND$" AND NOT (variable MATCHES "_headers_" OR variable MATCHES "_HEADERS_"))
            string(TOLOWER "${variable}" variable_lower)
            list(APPEND found_packages_lower "${variable_lower}")
            list(APPEND found_packages "${variable}")
        endif()
    endforeach()

    #message("found_packages_lower: ${found_packages_lower}")
    foreach(found_package IN LISTS found_packages)
        string(TOLOWER "${found_package}" found_package_lower)
        count("${found_packages_lower}" ${found_package_lower} package_count)
        index_of("${found_packages_lower}" ${found_package_lower} index)
        index_of("${found_packages_lower}" ${found_package_lower} index)
        math(EXPR package_count "${package_count} - 1")
        math(EXPR keep_index "${package_count} + ${index}")
        #message("  ${found_package} = ${${found_packag}} count:${package_count} index: ${index} keep_index: ${keep_index}")

        list(GET found_packages ${keep_index} keep_found_package)
        #list(FIND packages ${keep_found_package} index)

        string(REPLACE "_FOUND" "" package ${keep_found_package})
        string(REPLACE "_found" "" package ${package}) 

        list(FIND packages ${package} index)

        if(index EQUAL -1)
            list(APPEND packages ${package})
        endif()

        set(PACKAGES ${packages} PARENT_SCOPE)

    endforeach()

endfunction()

function(get_package_targets PACKAGE RETURN_VALUE)
    if(DEFINED ${PACKAGE}_TARGETS)
        set(RETURN_VALUE ${${PACKAGE}_TARGETS} PARENT_SCOPE)
    endif()
endfunction()
