find_package(PkgConfig REQUIRED)
pkg_check_modules(PROJ REQUIRED proj)
find_package(Eigen3 REQUIRED)
set(Eigen3_TARGETS Eigen3::Eigen)
find_package(OpenCV REQUIRED)

find_package(OpenDrive REQUIRED)
set(OpenDrive_TARGETS OpenDrive::OpenDrive)


if(TARGET adore_map)
    target_link_libraries(adore_map PRIVATE ${PROJ_LIBRARIES} ${OpenCV_LIBS})
endif()

