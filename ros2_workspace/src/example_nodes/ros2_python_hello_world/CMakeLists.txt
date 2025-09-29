cmake_minimum_required(VERSION 3.8)

get_filename_component(CURRENT_DIR_NAME ${CMAKE_CURRENT_SOURCE_DIR} NAME)
string(TOLOWER ${CURRENT_DIR_NAME} PROJECT)
project(${PROJECT})

find_package(ament_cmake REQUIRED)
find_package(ament_cmake_python REQUIRED)

# Install Python package (this creates the executables in bin/)
ament_python_install_package(${PROJECT_NAME})

# After Python package is installed, copy all executables to lib/package_name/
install(CODE "
  # Create the lib/package_name directory
  file(MAKE_DIRECTORY \"\${CMAKE_INSTALL_PREFIX}/lib/${PROJECT_NAME}\")
  
  # Find all executables in bin/ that start with our package name
  file(GLOB PACKAGE_EXECUTABLES \"\${CMAKE_INSTALL_PREFIX}/bin/${PROJECT_NAME}*\")
  
  # Copy each executable to lib/package_name/
  foreach(EXECUTABLE \${PACKAGE_EXECUTABLES})
    get_filename_component(EXEC_NAME \${EXECUTABLE} NAME)
    file(COPY \${EXECUTABLE} 
         DESTINATION \"\${CMAKE_INSTALL_PREFIX}/lib/${PROJECT_NAME}/\"
         FILE_PERMISSIONS OWNER_READ OWNER_WRITE OWNER_EXECUTE GROUP_READ GROUP_EXECUTE WORLD_READ WORLD_EXECUTE)
    message(STATUS \"Copied \${EXEC_NAME} to lib/${PROJECT_NAME}/\")
  endforeach()
")

# Install resource files  
install(
  DIRECTORY resource/
  DESTINATION share/ament_index/resource_index/packages/
  FILES_MATCHING PATTERN "${PROJECT_NAME}"
)

install(FILES package.xml
  DESTINATION share/${PROJECT_NAME}/
)

ament_package()
