#include <cmath>

#include <chrono>
#include <iomanip> // for std::fixed and std::setprecision
#include <iostream>

#include "adore_math/PiecewisePolynomial.h"

int
main()
{
  // Generate some realistic data for testing
  const int           numPoints = 31;
  std::vector<double> xValues, yValues, weights, x_hs, y_interpolated;

  // Generate x values (e.g., time points)
  for( int i = 0; i < numPoints; ++i )
  {
    double x = i * 0.1; // Adjust the interval as needed
    xValues.push_back( x );
  }
  // Generate x values (e.g., time points)
  for( int i = 0; i < 61; ++i )
  {
    double x = i * 0.05; // Adjust the interval as needed
    x_hs.push_back( x );
  }

  // Generate y values (e.g., some function + noise)
  for( const auto &x : xValues )
  {
    double y = 2 * x + sin( x ); // Sine function with added noise
    yValues.push_back( y );
  }

  // Generate weights (e.g., based on measurement errors)
  for( int i = 0; i < numPoints; ++i )
  {
    double weight = 1.0; // Adjust the weight range as needed
    weights.push_back( weight );
  }

  // Create an instance of your cubic spline class
  adore::math::PiecewisePolynomial cubicSpline;

  // Measure time using chrono
  auto start = std::chrono::high_resolution_clock::now(); // Start the clock

  // Apply the cubic spline smoother
  auto result = cubicSpline.linearPiecewise( xValues, yValues );
  cubicSpline.LinearPiecewiseEvaluation( y_interpolated, x_hs, result );

  auto stop           = std::chrono::high_resolution_clock::now();                             // Stop the clock
  auto duration_micro = std::chrono::duration_cast<std::chrono::microseconds>( stop - start ); // Calculate the duration in milliseconds
  auto duration_milli = std::chrono::duration_cast<std::chrono::milliseconds>( stop - start ); // Calculate the duration in milliseconds
  std::cout << "Time taken by function: " << duration_micro.count() << " microseconds" << std::endl;
  std::cout << "Time taken by function: " << duration_milli.count() << " milliseconds" << std::endl;
  // Print the results
  std::cout << "Cubic Spline Smoother Results:\n";
  std::cout << "breaks: ";
  for( const auto &value : result.breaks )
    std::cout << value << " ";
  std::cout << "\ncoef1: ";
  for( const auto &value : result.coef1 )
    std::cout << value << " ";
  std::cout << "\ncoef2: ";
  for( const auto &value : result.coef2 )
    std::cout << value << " ";
  std::cout << "\ncoef3: ";
  for( const auto &value : result.coef3 )
    std::cout << value << " ";
  std::cout << "\ncoef4: ";
  for( const auto &value : result.coef4 )
    std::cout << value << " ";
  std::cout << "\ny: ";
  for( const auto &value : yValues )
    std::cout << value << " ";
  std::cout << "\nyhs: ";
  for( const auto &value : y_interpolated )
    std::cout << value << " ";
  std::cout << std::endl;
}
