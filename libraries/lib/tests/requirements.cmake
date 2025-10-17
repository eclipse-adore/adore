find_package(GTest REQUIRED)

if(TARGET unit_test_runner)
    file(GLOB_RECURSE TEST_SOURCES "${CMAKE_CURRENT_LIST_DIR}/src/*.cpp")
    
    if(TEST_SOURCES)
        target_sources(unit_test_runner PRIVATE ${TEST_SOURCES})
    endif()
    
    target_link_libraries(unit_test_runner PRIVATE GTest::gtest GTest::gtest_main)
    
    if(UNIX)
        target_link_libraries(unit_test_runner PRIVATE pthread)
    endif()
endif()
