# Library Testing

This document describes how to work with tests in the ADORe libraries system.

## Running Unit Tests

To run all library unit tests:
```bash
cd libraries
make test
```

If the test binary hasn't been built yet, you'll see an error prompting you to build first:
```bash
cd libraries
make build
make test
```

The unit test runner is located at `build/bin/unit_test_runner` after building.

## Creating a New Unit Test

Unit tests use Google Test (GTest) and are automatically discovered and built by the system.

### Step 1: Create Your Test File

Add a new test `.cpp` file in `lib/tests/src/`:
```bash
touch lib/tests/src/my_feature_unit_tests.cpp
```

### Step 2: Write Your Tests
```cpp
#include <gtest/gtest.h>
#include "my_library/my_feature.h"

class MyFeatureTest : public ::testing::Test {
protected:
  void SetUp() override {
    // Setup code here
  }

  void TearDown() override {
    // Cleanup code here
  }
};

TEST_F(MyFeatureTest, BasicFunctionality) {
  EXPECT_EQ(1 + 1, 2);
  ASSERT_TRUE(true);
}

TEST_F(MyFeatureTest, AnotherTest) {
  EXPECT_NE(1, 2);
}
```

### Step 3: Build and Run
```bash
make build
make test
```

All `.cpp` files in `lib/tests/src/` are automatically compiled and linked into the test runner.

## Creating a Simple Test Program

Test programs are standalone executables used for manual testing, debugging, or demonstrations.

### Step 1: Create a Test Program Directory
```bash
mkdir -p lib/test_programs/my_test_program
```

### Step 2: Write Your Program

Create `lib/test_programs/my_test_program/my_test_program.cpp`:
```cpp
#include <iostream>
#include "my_library/my_feature.h"

int main() {
    std::cout << "Testing my feature..." << std::endl;
    
    // Your test code here
    
    std::cout << "Test complete!" << std::endl;
    return 0;
}
```

### Step 3: Add Dependencies (if needed)

If your test program needs external libraries, create `lib/test_programs/my_test_program/requirements.cmake`:
```cmake
find_package(Eigen3 REQUIRED)
set(Eigen3_TARGETS Eigen3::Eigen)
```

And optionally `requirements.system` for system packages:
```
libeigen3-dev
```

### Step 4: Build and Run

The build system automatically detects any `.cpp` file with a `main()` function and creates an executable.
```bash
make build
./build/bin/my_test_program
```

## Test Program vs Unit Test: When to Use Which

### Use Unit Tests When:
- Testing specific functions or classes
- Verifying correctness with assertions
- Running automated tests in CI/CD
- Testing edge cases and error conditions
- Need test fixtures and setup/teardown

### Use Test Programs When:
- Manual testing or debugging
- Demonstrating library usage
- Performance benchmarking
- Interactive testing
- Generating visual output or files

## Directory Structure
```
lib/
├── tests/                          # Unit tests
│   ├── src/                        # Test source files (auto-discovered)
│   │   ├── feature1_tests.cpp
│   │   └── feature2_tests.cpp
│   ├── unit_test_runner.cpp        # Test runner main()
│   └── requirements.cmake          # GTest dependencies
│
└── test_programs/                  # Standalone test programs
    ├── my_test/
    │   ├── my_test.cpp             # Must have main()
    │   ├── requirements.cmake      # Optional dependencies
    │   └── requirements.system     # Optional system packages
    └── another_test/
        └── another_test.cpp
```

## Excluding Tests from Build

To prevent a test from being built, add it to `.cmakeignore`:
```bash
echo "lib/tests/src/broken_test.cpp" >> .cmakeignore
echo "lib/test_programs/my_test" >> .cmakeignore
```

## Common GTest Assertions
```cpp
EXPECT_EQ(a, b);      // a == b
EXPECT_NE(a, b);      // a != b
EXPECT_LT(a, b);      // a < b
EXPECT_LE(a, b);      // a <= b
EXPECT_GT(a, b);      // a > b
EXPECT_GE(a, b);      // a >= b
EXPECT_TRUE(cond);    // condition is true
EXPECT_FALSE(cond);   // condition is false
EXPECT_NEAR(a, b, e); // |a - b| <= e

ASSERT_EQ(a, b);      // Same as EXPECT_* but stops test on failure
```

## Tips

1. **Naming Convention**: Name test files with `_tests.cpp` or `_unit_tests.cpp` suffix
2. **Test Organization**: Group related tests in the same file
3. **Test Fixtures**: Use `TEST_F` with fixture classes for shared setup
4. **Fast Tests**: Keep unit tests fast (< 1ms per test ideally)
5. **Descriptive Names**: Use clear test names that describe what is being tested
6. **One Assertion Focus**: Each test should focus on one specific behavior

## Example: Complete Unit Test
```cpp
#include <gtest/gtest.h>
#include <vector>
#include "adore_math/PiecewisePolynomial.h"

class PiecewisePolynomialTest : public ::testing::Test {
protected:
  void SetUp() override {
    for (int i = 0; i < 10; ++i) {
      xValues.push_back(i * 0.1);
      yValues.push_back(i * 0.1);
    }
  }

  std::vector<double> xValues;
  std::vector<double> yValues;
  adore::math::PiecewisePolynomial poly;
};

TEST_F(PiecewisePolynomialTest, ReturnsCorrectSize) {
  auto result = poly.linearPiecewise(xValues, yValues);
  EXPECT_EQ(result.breaks.size(), xValues.size());
}

TEST_F(PiecewisePolynomialTest, HandlesEmptyInput) {
  std::vector<double> empty;
  auto result = poly.linearPiecewise(empty, empty);
  EXPECT_TRUE(result.breaks.empty());
}
```

## Troubleshooting

**Tests not found after adding new test file:**
- Rebuild: `make clean && make build`
- Check file is in `lib/tests/src/`
- Verify file not in `.cmakeignore`

**Linking errors:**
- Add missing dependencies to `lib/tests/requirements.cmake`
- Check library is built and available

**Test program not created:**
- Ensure file has `int main()` function
- Check file not in `.cmakeignore`
- Rebuild project
