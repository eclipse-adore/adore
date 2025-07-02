cmake_minimum_required(VERSION 3.10)
project(sumo_installer_deb NONE)

set(CPACK_PACKAGE_NAME "sumo-installer")
set(CPACK_PACKAGE_VERSION "1.0.0")
set(CPACK_PACKAGE_CONTACT "you@example.com")
set(CPACK_DEBIAN_PACKAGE_MAINTAINER "Your Name")
set(CPACK_GENERATOR "DEB")

# Correctly set postinst path and ensure it's executable
set(CPACK_DEBIAN_PACKAGE_CONTROL_EXTRA "${CMAKE_SOURCE_DIR}/debian/postinst")

include(CPack)

