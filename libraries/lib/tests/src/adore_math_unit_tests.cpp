/********************************************************************************
 * Copyright (c) 2025 Contributors to the Eclipse Foundation
 *
 * See the NOTICE file(s) distributed with this work for additional
 * information regarding copyright ownership.
 *
 * This program and the accompanying materials are made available under the
 * terms of the Eclipse Public License 2.0 which is available at
 * https://www.eclipse.org/legal/epl-2.0
 *
 * SPDX-License-Identifier: EPL-2.0
 ********************************************************************************/
#include <cmath>
#include <chrono>
#include <gtest/gtest.h>
#include "adore_math/PiecewisePolynomial.h"

class PiecewisePolynomialTest : public ::testing::Test {
protected:
  void SetUp() override {
    const int numPoints = 31;
    
    for (int i = 0; i < numPoints; ++i) {
      double x = i * 0.1;
      xValues.push_back(x);
    }
    
    for (int i = 0; i < 61; ++i) {
      double x = i * 0.05;
      x_hs.push_back(x);
    }
    
    for (const auto &x : xValues) {
      double y = 2 * x + sin(x);
      yValues.push_back(y);
    }
    
    for (int i = 0; i < numPoints; ++i) {
      weights.push_back(1.0);
    }
  }

  std::vector<double> xValues;
  std::vector<double> yValues;
  std::vector<double> weights;
  std::vector<double> x_hs;
  adore::math::PiecewisePolynomial cubicSpline;
};

TEST_F(PiecewisePolynomialTest, LinearPiecewiseBasicFunctionality) {
  auto result = cubicSpline.linearPiecewise(xValues, yValues);
  
  ASSERT_FALSE(result.breaks.empty());
  ASSERT_FALSE(result.coef1.empty());
  ASSERT_FALSE(result.coef2.empty());
  
  EXPECT_EQ(result.breaks.size(), xValues.size());
}

TEST_F(PiecewisePolynomialTest, LinearPiecewiseEvaluation) {
  std::vector<double> y_interpolated;
  
  auto result = cubicSpline.linearPiecewise(xValues, yValues);
  cubicSpline.LinearPiecewiseEvaluation(y_interpolated, x_hs, result);
  
  ASSERT_EQ(y_interpolated.size(), x_hs.size());
  
  for (const auto &val : y_interpolated) {
    EXPECT_FALSE(std::isnan(val));
    EXPECT_FALSE(std::isinf(val));
  }
}

TEST_F(PiecewisePolynomialTest, PerformanceTest) {
  std::vector<double> y_interpolated;
  
  auto start = std::chrono::high_resolution_clock::now();
  
  auto result = cubicSpline.linearPiecewise(xValues, yValues);
  cubicSpline.LinearPiecewiseEvaluation(y_interpolated, x_hs, result);
  
  auto stop = std::chrono::high_resolution_clock::now();
  auto duration_micro = std::chrono::duration_cast<std::chrono::microseconds>(stop - start);
  
  std::cout << "Performance: " << duration_micro.count() << " microseconds" << std::endl;
  
  EXPECT_LT(duration_micro.count(), 10000);
}

TEST_F(PiecewisePolynomialTest, InterpolationAccuracy) {
  std::vector<double> y_interpolated;
  
  auto result = cubicSpline.linearPiecewise(xValues, yValues);
  cubicSpline.LinearPiecewiseEvaluation(y_interpolated, x_hs, result);
  
  for (size_t i = 0; i < x_hs.size(); ++i) {
    double expected = 2 * x_hs[i] + sin(x_hs[i]);
    EXPECT_NEAR(y_interpolated[i], expected, 0.5);
  }
}
