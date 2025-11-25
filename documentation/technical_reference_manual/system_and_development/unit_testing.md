````markdown
# Testing in ADORe

This document explains how tests are structured in ADORe, using:

- `adore_math` – a pure C++ library package
- `adore_math_conversions` – a ROS 2–integrated C++ package

and how to run them via `colcon` and the `Justfile` helpers.

This document focuses on **unit & package-level tests**, with system tests briefly referenced at the end.

---

## Where tests live

Every package is responsible for its own tests:

- Tests go into a `test/` directory **next to** `src/` and `include/`.
- CMake wires them up using `ament_cmake_gtest`.

### Example: `adore_math`

Structure:

```text
adore_math/
  include/adore_math/...
  src/...
  test/
    angle_test.cpp
    distance_test.cpp
    polynomian_test.cpp
    CMakeLists.txt
````

Key CMake snippet in `adore_math/CMakeLists.txt`:

```cmake
# Tests
# -------------------------------------------------------------------
if(BUILD_TESTING)
  find_package(ament_cmake_gtest REQUIRED)

  # Library under test, used by test/CMakeLists.txt
  set(ADORE_TEST_LIB_TARGET ${PROJECT_NAME})

  add_subdirectory(test)
endif()
```

The `test/CMakeLists.txt` then discovers test files and registers them:

```cmake
# Tests for adore_math
# Expects:
#   - ADORE_TEST_LIB_TARGET set by parent CMakeLists.txt
#   - ament_cmake_gtest already found

file(GLOB ADORE_MATH_TEST_SOURCES CONFIGURE_DEPENDS
  "*.cpp"
)

foreach(test_src ${ADORE_MATH_TEST_SOURCES})
  get_filename_component(test_name ${test_src} NAME_WE)

  ament_add_gtest(${test_name} ${test_src})

  if(TARGET ${test_name})

    target_link_libraries(${test_name}
      ${ADORE_TEST_LIB_TARGET}
      Eigen3::Eigen
    )

    target_include_directories(${test_name}
      PRIVATE
        ${CMAKE_CURRENT_SOURCE_DIR}/../include
    )
  endif()
endforeach()
```

**Takeaways for library-style packages:**

* Put tests in `test/`.
* Use a `test/CMakeLists.txt` with `ament_add_gtest`.
* Link tests against the library target (`${PROJECT_NAME}` or similar).
* Use `if(BUILD_TESTING)` in the main `CMakeLists.txt` and call `add_subdirectory(test)`.

---

### Example: `adore_math_conversions`

Structure:

```text
adore_math_conversions/
  include/...
  src/adore_math_conversions.cpp
  test/test_adore_math_conversions.cpp
```

Key CMake snippet in `adore_math_conversions/CMakeLists.txt`:

```cmake
# Tests
if(BUILD_TESTING)
  find_package(ament_cmake_gtest REQUIRED)

  ament_add_gtest(test_adore_math_conversions
    test/test_adore_math_conversions.cpp
  )

  if(TARGET test_adore_math_conversions)
    # Link against the library under test so it reuses the same code
    target_link_libraries(test_adore_math_conversions
      ${PROJECT_NAME}
    )
  endif()
endif()

ament_package()
```

**Takeaways for node / conversion / ROS packages:**

* Put tests in `test/` and list them directly in the main `CMakeLists.txt` or follow adore_decision_maker structure with separate `CMakeLists.txt` in test directory.
* Use `ament_add_gtest(<test_target> test/<file>.cpp)`.
* Link against `${PROJECT_NAME}` (or the relevant library target).

---

## How to write C++ tests

Both `adore_math` and `adore_math_conversions` use **GoogleTest (GTest)** via `ament_cmake_gtest`.

### Test file template

A typical test file looks like this:

```cpp

#include <gtest/gtest.h>

// Include the code under test
#include <adore_math/angles.h>

TEST(Angles, DegreesToRadiansAndBack)
{
  const double deg = 100.0;
  const double rad = adore::math::to_radians(deg);

  EXPECT_NEAR(adore::math::to_degrees(rad), deg, 1e-9);
}
```

For more complex tests, you can use fixtures (`TEST_F`) or helpers:

```cpp
class PiecewisePolynomialTest : public ::testing::Test
{
protected:
  void SetUp() override
  {
    // Prepare x/y data, etc.
  }

  // Fields: cubicSpline, xValues, yValues, ...
};

TEST_F(PiecewisePolynomialTest, InterpolationAccuracy)
{
  std::vector<double> y_interpolated;
  auto result = cubicSpline.linearPiecewise(xValues, yValues);
  cubicSpline.LinearPiecewiseEvaluation(y_interpolated, x_hs, result);

  for (size_t i = 0; i < x_hs.size(); ++i)
  {
    double expected = 2 * x_hs[i] + std::sin(x_hs[i]);
    EXPECT_NEAR(y_interpolated[i], expected, 0.5);
  }
}
```

### Guidelines / expectations

* **Small and deterministic**

  * Avoid non-deterministic behavior (time, randomness, global state).
  * If you measure performance, keep it short and deterministic – it still needs to pass in CI.

* **Round-trip & invariants**

  * The conversion tests in `adore_math_conversions` use **round-trip checks**:

    * convert C++ → ROS msg → C++ and compare the result.
  * For math utilities:

    * test symmetry, bounds, and known identities (e.g. degrees ↔ radians).

* **Naming**

  * Prefer `TEST(Category, Behavior)` where `Category` is a class/module and `Behavior` is what you expect.
  * File names generally mirror the unit under test: `distance_test.cpp`, `angle_test.cpp`, …

* **Include paths**

  * Include public headers from `include/` and avoid reaching into `src/` whenever possible.
  * If you really need internal details, consider adding a dedicated internal header rather than including `.cpp` directly.

---

## Running tests

###  Running tests inside the dev container

The dev container has ROS and all build tools installed.

1. Start or attach to the dev container:

   ```bash
   just dev
   ```

2. Inside the container, from the repo root:

   * Run the whole test suite:

     ```bash
     just test_ws
     ```

     (This uses the same `Justfile` and will run `colcon test` inside the container.)

   * Or run `colcon` manually:

     ```bash
     cd .colcon_workspace
     colcon test --packages-select adore_math adore_math_conversions
     colcon test-result --all --verbose
     ```

---

### Running tests for a single package

From the repo root (host or dev container):

```bash
cd .colcon_workspace
colcon test --packages-select adore_math
colcon test-result --all --verbose
```

Replace `adore_math` with `adore_math_conversions` or any other package name.

**Tips:**

* You can pass multiple packages to `--packages-select`:

  ```bash
  colcon test --packages-select adore_math adore_math_conversions
  ```
* If you are iterating on a single test, this makes the cycle much faster than running the whole workspace.

---

###  Running a single test binary

Sometimes you just want to run one specific test executable directly (e.g., to debug with `gdb`).

After building and running `colcon test` at least once, the test binaries will be in the `build/` directory. For example:

```bash
cd .colcon_workspace
./build/adore_math/angle_test
./build/adore_math_conversions/test_adore_math_conversions
```

You can also attach a debugger:

```bash
gdb --args ./build/adore_math/angle_test
```

> Path details are managed by `ament_cmake_gtest` and `colcon` – if in doubt, inspect the `build/<pkg>` directory or re-run `colcon test` to regenerate.

---

###  System tests

System tests are orchestrated separately:

```bash
just test_system
```

please see [System Tests](technical_reference_manual/system_and_development/system_tests.md)

---

### CI: tests + docs

For a local approximation of CI:

```bash
just ci
```

This:

* Uses the CI Docker image.
* Runs tests and documentation checks via `.docker/scripts/run_ci.sh`.

Use this when you want a **“what CI will do”** check before pushing changes.

---

## 5. How to add tests to a new package

### Step 1: Create `test/` directory

Inside your package:

```text
my_package/
  include/...
  src/...
  test/
    my_feature_test.cpp
```

### Step 2: Add GTest code

In `test/my_feature_test.cpp`:

```cpp
#include <gtest/gtest.h>
#include <my_package/my_feature.hpp>

TEST(MyFeature, DoesWhatItSays)
{
  const auto result = my_package::do_thing(42);
  EXPECT_EQ(result, 123);
}
```

Follow the patterns from `adore_math` and `adore_math_conversions`.

### Step 3: Wire it up in CMake

**Option A: test subdirectory (library-style, like `adore_math`)**

`CMakeLists.txt`:

```cmake
if(BUILD_TESTING)
  find_package(ament_cmake_gtest REQUIRED)
  set(ADORE_TEST_LIB_TARGET ${PROJECT_NAME})
  add_subdirectory(test)
endif()
```

`test/CMakeLists.txt` (very similar to `adore_math`):

```cmake
file(GLOB MY_PACKAGE_TEST_SOURCES CONFIGURE_DEPENDS
  "*.cpp"
)

foreach(test_src ${MY_PACKAGE_TEST_SOURCES})
  get_filename_component(test_name ${test_src} NAME_WE)
  ament_add_gtest(${test_name} ${test_src})

  if(TARGET ${test_name})
    target_link_libraries(${test_name}
      ${ADORE_TEST_LIB_TARGET}
      # extra deps...
    )
  endif()
endforeach()
```

**Option B: direct registration (like `adore_math_conversions`)**

`CMakeLists.txt`:

```cmake
if(BUILD_TESTING)
  find_package(ament_cmake_gtest REQUIRED)

  ament_add_gtest(test_my_feature
    test/my_feature_test.cpp
  )

  if(TARGET test_my_feature)
    target_link_libraries(test_my_feature
      ${PROJECT_NAME}
    )
  endif()
endif()
```

### Step 4: Run the tests

From the repo root:

```bash
just test_ws
# or
cd .colcon_workspace
colcon test --packages-select my_package
colcon test-result --all --verbose
```

---

## 6. Summary

* **Tests live in `test/` inside each package.**
* **Use GTest via `ament_cmake_gtest`** and follow the patterns shown in:

  * `adore_math/test/CMakeLists.txt`
  * `adore_math_conversions/CMakeLists.txt`
* **Run tests** using:

  * `just test_ws` – all unit tests in the workspace.
  * `colcon test --packages-select <pkg>` – a specific package.
  * `just test_system` – system-level tests.
  * `just ci` – approximate CI: tests + docs, in a container.
* **Write tests that are small, deterministic, and focused on invariants and round-trips**, mirroring the approach in `adore_math` and `adore_math_conversions`.
