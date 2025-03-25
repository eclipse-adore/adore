
message("target_functions.cmake loaded")

include(CMakePackageConfigHelpers)

function(get_targets targets)
    set(${result} "")

    get_property(targets GLOBAL PROPERTY GLOBAL_TARGETS)
    foreach(target ${targets})
        #message("target: ${target}")
        get_target_property(target_type ${target} TYPE)
        if(NOT target_type STREQUAL "EXECUTABLE")
            list(APPEND ${result} ${target})
        endif()
    endforeach()
    set(${targets} ${result} PARENT_SCOPE)
endfunction()

# Helper function to get all targets
function(get_all_targets result)
endfunction()

function(is_library PATH RETURN_VALUE)
    if(EXISTS "${PATH}/include" AND EXISTS "${PATH}/src")
        set(${RETURN_VALUE} TRUE PARENT_SCOPE)
    else()
        set(${RETURN_VALUE} FALSE PARENT_SCOPE)
    endif()
endfunction()

function(is_interface PATH RETURN_VALUE)
    if(EXISTS "${PATH}/include" AND NOT EXISTS "${PATH}/src")
        set(${RETURN_VALUE} TRUE PARENT_SCOPE)
    else()
        set(${RETURN_VALUE} FALSE PARENT_SCOPE)
    endif()
endfunction()



function(is_executable TARGET_NAME RETURN_VALUE)
    get_target_property(target_type ${TARGET_NAME} TYPE)
    if(target_type STREQUAL "EXECUTABLE")
        set(RETURN_VALUE TRUE PARENT_SCOPE)
    else()
        set(RETURN_VALUE FALSE PARENT_SCOPE)
    endif()
endfunction()

macro(generate_library_targets SOURCE_DIRECTORY)


    message("")
    message("Generating CMake library targets...")
    set(cmakeignore_file "${CMAKE_SOURCE_DIR}/.cmakeignore")
    message("  Using .cmakeignore: ${cmakeignore_file}")
    #message("")

    #find_all_requirements(${CMAKE_SOURCE_DIR}/lib)
    file(GLOB directories CONFIGURE_DEPENDS "${SOURCE_DIRECTORY}/*")

    foreach(directory ${directories})
        #message("directory:${directory}")
        is_library(${directory} is_library_return_value)
        is_interface(${directory} is_interface_return_value)
        #message(" is_library: ${is_library_return_value}")
        #message(" is_interface: ${is_interface_return_value}")
        if(is_library_return_value OR is_interface_return_value)
            set(ignore_path FALSE)
            cmakeignore(${directory} ${cmakeignore_file} RETURN_VALUE)
            set(ignore_path ${RETURN_VALUE})
            #message("  path: ${directory} ignore: ${ignore_path}")
            if(NOT ignore_path)
                #message(STATUS "Processing path: ${path}")
                # Add your logic here for the paths that are not ignored

                if(IS_DIRECTORY ${directory})
                    get_filename_component(library_name ${directory} NAME)
                    #message("")
                    message("  Generating library target: ${library_name}")
                    message("    directory: ${directory}")

                    #message(STATUS "Library: ${library_name}")

                    if(is_library_return_value)
                        add_library(${library_name} STATIC)
                        file(GLOB_RECURSE library_sources "${directory}/*.cpp")
                        target_sources(${library_name} PRIVATE ${library_sources})
                    else()
                        add_library(${library_name} INTERFACE)
                    endif()
                    target_include_directories( ${library_name} INTERFACE 
                        $<BUILD_INTERFACE:${CMAKE_SOURCE_DIR}/lib/${library_name}/include>
                        $<INSTALL_INTERFACE:${CMAKE_INSTALL_INCLUDEDIR}>
                        )

                    if (EXISTS ${CMAKE_CURRENT_SOURCE_DIR}/requirements.cmake)
                        include("${CMAKE_CURRENT_SOURCE_DIR}/lib/${library_name}/requirements.cmake")
                    endif()



                    set_target_properties(${library_name} PROPERTIES
                        ARCHIVE_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/lib"
                        )

                    set_target_properties(${library_name} PROPERTIES
                        OUTPUT_NAME "${library_name}"
                        )

                    #target_include_directories(${library_name} PRIVATE "${${variable}}")
                    file(COPY "${CMAKE_SOURCE_DIR}/lib/${library_name}/include" DESTINATION "${CMAKE_BINARY_DIR}/lib/${library_name}")

                    include(${CMAKE_SOURCE_DIR}/cmake/InstallTargets.cmake)

                endif()
                #message("")
            else()
                message("  The directory: ${directory}") 
                message("  is in the .cmakeignore file, skipping creation of target")
                message("  remove this pattern from the .cmakeignore file to auto-generate the target.")
                message("")
            endif()
        else()
            message("  The directory: ${directory} is not a library.")
            message("    Skipping auto-target creation.")
            message("    Add an `include` and `source` directory to:${directory} to auto-generate a target for this directory.")
            message("")
        endif()
    endforeach()

    #message("  adding include directories and link libraries to generated library targets...")
    get_property(targets DIRECTORY PROPERTY BUILDSYSTEM_TARGETS)
    foreach(target ${targets})
        add_all_target_include_directories(${target})
        add_all_target_link_libraries(${target})
    endforeach()

endmacro()

macro(add_all_target_include_directories NEW_TARGET)
    #message("    Adding all target include directories for target: '${NEW_TARGET}'")
    get_property(targets DIRECTORY PROPERTY BUILDSYSTEM_TARGETS)
    foreach(target ${targets})
        get_target_property(target_type ${NEW_TARGET} TYPE)
        if(NEW_TARGET STREQUAL target)
            continue()
        endif()
        if(target_type STREQUAL "UTILITY")
            continue()
        endif()
        if(NEW_TARGET_TYPE STREQUAL "STATIC_LIBRARY")
            continue()
        endif()
        if(NEW_TARGET_TYPE STREQUAL "INTERFACE_LIBRARY")
            continue()
        endif()

        message("    Adding target include directories for target: '${NEW_TARGET}' of type: ${NEW_TARGET_TYPE} from target: ${target} of type: ${target_type}")
        target_include_directories(${NEW_TARGET} PRIVATE "${CMAKE_SOURCE_DIR}/lib/${target}/include")
    endforeach()
endmacro()

function(check_link_library src_target dest_target result)
    get_target_property(dest_target_libraries ${dest_target} LINK_LIBRARIES)

    list(FIND dest_target_libraries ${src_target} index)

    if(index EQUAL -1)
        set(${result} FALSE PARENT_SCOPE)
    else()
        set(${result} TRUE PARENT_SCOPE)
    endif()
endfunction()

macro(add_all_target_link_libraries NEW_TARGET)

    find_all_requirements("${CMAKE_SOURCE_DIR}/lib")

    #message("    Adding all target link libraries for: ${NEW_TARGET}")
    get_property(targets DIRECTORY PROPERTY BUILDSYSTEM_TARGETS)
    foreach(target ${targets})

        get_target_property(NEW_TARGET_TYPE ${NEW_TARGET} TYPE)
        get_target_property(target_type ${target} TYPE)
        #message("      NEW_TARGET: '${target}' TARGET:'${target}'")
        if(target_type STREQUAL "EXECUTABLE")
            #message("      '${target}' is an executable target, skipping linking: '${target}' to: '${NEW_TARGET}'")
            continue()
        endif()
        if(NEW_TARGET_TYPE STREQUAL "UTILITY" OR target_type STREQUAL "UTILITY")
            continue()
        endif()
        if(${NEW_TARGET} STREQUAL ${target})
            continue()
        endif()

        #message("      linking: '${target}' with target type: '${target_type}' to: '${NEW_TARGET}' with target type: ${NEW_TARGET_TYPE}")

        check_link_library(${target} ${NEW_TARGET} already_linked)
        if(already_linked)
            continue()
        endif()

        if(NEW_TARGET_TYPE STREQUAL "INTERFACE_LIBRARY")
            #message("      target_link_libraries: INTERFACE")
            target_link_libraries(${NEW_TARGET} INTERFACE "${target}")
        else()
            #message("      target_link_libraries: STATIC")
            target_link_libraries(${NEW_TARGET} PRIVATE "${target}")
        endif()
    endforeach()

    #message("    Adding all package link libraries for: ${NEW_TARGET}")
    get_cmake_packages(PACKAGES)
    foreach(package ${PACKAGES}) 
        #message("    package: ${package}")
        #message("    package_TARGETS: ${${package}_TARGETS}")
        get_package_targets(${PACKAGES} RETURN_VALUE)
        set(package_targets ${RETURN_VALUE})
        foreach(package_target ${${package}_TARGETS})
            #message("      linking: '${package_target}' to: '${NEW_TARGET}'")
            get_target_property(target_type ${NEW_TARGET} TYPE)
            if(target_type STREQUAL "INTERFACE_LIBRARY")
                target_link_libraries(${NEW_TARGET} INTERFACE "${package_target}")
                #elseif(target_type STREQUAL "STATIC_LIBRARY")
            elseif(target_type STREQUAL "UTILITY")
                #message("      target: '${package_target}' is a UTILITY skipping linking to: '${NEW_TARGET}'")
            else()
                target_link_libraries(${NEW_TARGET} PRIVATE "${package_target}")
            endif()

        endforeach()
    endforeach()
endmacro()




macro(link_package_targets PACKAGE TARGET)
    find_package(${PACKAGE} REQUIRED)
    get_property(${PACKAGE}_IMPORTED_TARGETS GLOBAL PROPERTY IMPORTED_TARGETS)
    foreach(package_target ${${PACKAGE}_IMPORTED_TARGETS})
        target_link_libraries(${TARGET} PRIVATE ${package_target})
    endforeach()
endmacro()

macro(generate_executable_targets folder)
    execute_process(
        COMMAND grep -rlPz --include=*.cpp "int\\s+main\\s*\\(" ${folder}
        RESULT_VARIABLE grep_result
        OUTPUT_VARIABLE grep_output
        )

    if(grep_result EQUAL 0)
        string(REGEX REPLACE "\n" ";" source_files_with_main ${grep_output})

        find_all_packages("${CMAKE_SOURCE_DIR}/build/share")
        find_all_packages("${CMAKE_SOURCE_DIR}/../vendor/mathematics_toolbox/eigen/build")

        set(cmakeignore_file "${CMAKE_SOURCE_DIR}/.cmakeignore")
        message("")
        message("Generating CMake executable targets...")
        message("  Using .cmakeignore: ${cmakeignore_file}")
        message("")
        foreach(source_file ${source_files_with_main})

            message("")
            set(ignore_path FALSE)
            cmakeignore(${source_file} ${cmakeignore_file} RETURN_VALUE)
            set(ignore_path ${RETURN_VALUE})
            if(NOT ignore_path)

                #message(STATUS "  Executable: ${source_file}")

                get_filename_component(file_name ${source_file} NAME_WE)
                set(executable_target "${file_name}")
                message("  Generating executable target: ${executable_target}")
                add_executable(${executable_target} ${source_file})

                add_all_target_include_directories(${executable_target})
                add_all_target_link_libraries(${executable_target})

                #target_compile_options(${file_name} PRIVATE -fpermissive)

                #find_all_requirements("${CMAKE_SOURCE_DIR}/lib")


                get_property(targets DIRECTORY PROPERTY BUILDSYSTEM_TARGETS)
                #message(STATUS "Defined exe targets:")
                foreach(target ${targets})
                    #message(STATUS "  TARGET: ${target_name}")
                    #target_include_directories(${file_name} PRIVATE $<TARGET_PROPERTY:${target},INTERFACE_INCLUDE_DIRECTORIES>)
                    get_target_property(target_type ${target} TYPE)
                    if(NOT "${target_type}" MATCHES "EXECUTABLE")
                        #target_link_libraries(${file_name} PRIVATE ${target})
                    endif()
                    #target_link_libraries(${file_name} PRIVATE Eigen3::Eigen)
                    #link_package_targets(${file_name} PRIVATE Eigen3)
                endforeach()



                get_cmake_property(variables VARIABLES)
                foreach(variable ${variables})
                    if(variable MATCHES "_headers_DIR$")
                        #message(STATUS "  adding include directories: ${file_name}:${target_name}")
                        #target_include_directories(${file_name} PRIVATE "${${variable}}")
                    endif()
                endforeach()




                set_target_properties(${file_name} PROPERTIES
                    RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin
                    )

            else()
                message("  The source file: ${source_file}") 
                message("  is in the .cmakeignore file, skipping creating executable.")
                message("  remove this pattern from the .cmakeignore file to auto-generate the target.")
                message("")
            endif()
        endforeach()
    else()
        message(STATUS "  No files with 'int main(' found in ${folder}. No executable targets to generate.")
    endif()
endmacro()

function(print_libraries)
    message(STATUS "Defined libraries/packages in the project:")

    # Retrieve the list of defined libraries/packages
    get_property(package_list GLOBAL PROPERTY PACKAGES)

    foreach(package ${package_list})
        message(STATUS " - ${package}")
    endforeach()
endfunction()


function(find_all_packages CMAKE_SHARE_DIR)

    list(APPEND CMAKE_PREFIX_PATH "${CMAKE_SHARE_DIR}")
    file(GLOB package_subdirs "${CMAKE_SHARE_DIR}/lib/*")
    foreach(package_dir ${package_subdirs})
        if(IS_DIRECTORY ${package_dir})
            get_filename_component(package_name ${package_dir} NAME)
            find_package(${package_name} REQUIRED)

            if(${package_name}_FOUND)
                get_cmake_property(_vars VARIABLES PARENT_SCOPE)
                foreach(_var ${_vars})
                    if(_var MATCHES "^${package_name}_.*")
                        set(${_var} ${${_var}} PARENT_SCOPE)
                    endif()
                endforeach()
            endif()
            if(${package_name}_FOUND)
                message(STATUS "Found package: ${package_name}")
            else()
                message(STATUS "Package ${package_name} not found.")
            endif()
        endif()
    endforeach()
endfunction()
