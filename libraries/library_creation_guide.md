# Library Creation Guide

The ADORe libraryes  CMake system automatically generates library targets based
on directory structure in the `lib/` folder.

## Library Types

### Static Library
```
lib/
└── my_library/
    ├── include/
    │   └── my_library/
    │       └── header.hpp
    └── src/
        └── implementation.cpp
```
- **Requires**: Both `include/` and `src/` directories
- **Generated**: `add_library(my_library STATIC)`
- **Auto-includes**: All `*.cpp` files in `src/`

### Interface Library (Header-only)
```
lib/
└── my_header_lib/
    └── include/
        └── my_header_lib/
            └── header<.hpp or .h>
```
- **Requires**: Only `include/` directory (no `src/`)
- **Generated**: `add_library(my_header_lib INTERFACE)`
- **Use case**: Header-only libraries, templates

## Executable Targets

Executable targets are automatically generated for any `.cpp` file containing `int main(`.

### Auto-Detection
```
lib/
├── my_library/
│   └── src/
│       └── library_code.cpp
└── test_programs/
    ├── demo_app/
    │   └── main.cpp              # Contains int main()
    └── unit_tests/
        └── test_runner.cpp       # Contains int main()
```

### Generated Targets
- **Target name**: Based on filename without extension
- **Example**: `demo_app/main.cpp` → `main` executable
- **Output**: Built to `build/bin/`
- **Auto-linking**: All library targets automatically linked

### Requirements
```cpp
// File: lib/examples/hello_world.cpp
#include <iostream>

int main() {  // This pattern triggers auto-generation
    std::cout << "Hello World!" << std::endl;
    return 0;
}
```

## Auto-Generated Features

- **Include directories**: Automatically set up for consumers
- **Linking**: All libraries auto-link to each other (configurable)
- **Output location**: Libraries built to `build/lib/`

## Exclusions

Add patterns to `.cmakeignore` to skip auto-generation:
```
lib/experimental_lib
lib/*/test
**/debug_*.cpp
```

## Dependencies

Create `lib/my_library/requirements.cmake` for external dependencies:
```cmake
find_package(SomePackage REQUIRED)
target_link_libraries(my_library PRIVATE SomePackage::SomePackage)
```

## Example

1. Create directory: `mkdir -p lib/math_utils/{include/math_utils,src}`
2. Add header: `lib/math_utils/include/math_utils/calculator.hpp`
3. Add source: `lib/math_utils/src/calculator.cpp`
4. Run `make build` - library/target `math_utils` is automatically created

## Consuming an Auto-generated Library

1. In the `CMakeLists.txt` for your program include the `adore_libraries.cmake` 
file. Inside the `ADORE CLI` docker context the environmental variable
`SOURCE_DIRECTORY` will be set. This can be used to locate the 
`adore_libraries.cmake`:
```cmake
include($ENV{SOURCE_DIRECTORY}/libraries/adore_libraries.cmake)

2. Create a `requirements.cmake` file in the same directory as your
`CMakeLists.txt` and add any special cmake requirements:
```cmake
include(requirements.cmake)
```

Example `requirements.cmake` file:
```cmake
find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(Eigen3 REQUIRED)
set(Eigen3_TARGETS Eigen3::Eigen)
```

3. Invoke the helper functions on your target provided by 
`adore_libraries.cmake` to auto link and include libraries:
```cmake
add_all_target_include_directories(${PROJECT})
add_all_target_link_libraries(${PROJECT})
```
