
include(GNUInstallDirs)

include(CMakePackageConfigHelpers)


install(
    TARGETS ${library_name}
    EXPORT ${library_name}Targets
    LIBRARY DESTINATION ${CMAKE_INSTALL_LIBDIR}
    ARCHIVE DESTINATION ${CMAKE_INSTALL_LIBDIR}
    RUNTIME DESTINATION ${CMAKE_INSTALL_BINDIR}
    INCLUDES DESTINATION ${CMAKE_INSTALL_INCLUDEDIR}
)



configure_package_config_file(
    "${CMAKE_SOURCE_DIR}/cmake/LibraryConfig.cmake.in"
    "${CMAKE_BINARY_DIR}/share/${library_name}/cmake/${library_name}Config.cmake"
    INSTALL_DESTINATION ${CMAKE_BINARY_DIR}/share/${library_name}/cmake
)


install(
    EXPORT ${library_name}Targets
    COMPONENT ${library_name}
    FILE ${library_name}Targets.cmake
    NAMESPACE ${library_name}::
    DESTINATION ${CMAKE_BINARY_DIR}/${library_name}/cmake
)

install(
    FILES "${PROJECT_BINARY_DIR}/${library_name}Config.cmake"
    DESTINATION ${CMAKE_BINARY_DIR}/share/${library_name}/cmake
    COMPONENT ${library_name}
)

export(
  TARGETS ${library_name}
  NAMESPACE ${library_name}::
  FILE ${CMAKE_BINARY_DIR}/share/${library_name}/cmake/${library_name}Targets.cmake
)


