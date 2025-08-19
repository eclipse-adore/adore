# Math Library for Autonomous Systems

## Overview
The **Math Library** provides mathematical tools and utilities essential for ADORe. 

---

## Features
- **Angle Utilities**:
  - Functions for angular operations like wrapping and delta computation.
- **Curvature Analysis**:
  - Compute curvature for trajectories or continuous paths.
- **Distance Calculations**:
  - templated distance metrics
- **Piecewise Polynomials**:
  - Evaluate and manage piecewise polynomials.
- **Spline Interpolation**:
  - Generate and evaluate cubic splines.
- **Eigen Integration**:
  - Utilities for matrix and vector operations using the Eigen library.

---

## Included Modules

### Angles
**File:** `angles.h`
- Provides utilities for angle normalization and conversion.
- Handles wrapping of angles to predefined ranges.

### Curvature
**File:** `curvature.hpp`
- Computes curvature for a given trajectory.
- Useful for trajectory evaluation and planning.

### Distance
**File:** `distance.h`
- Implements various distance metrics, including:

### Eigen Utilities
**File:** `eigen.h`
- Utilities for working with Eigen matrices and vectors.

### Piecewise Polynomial
**File:** `PiecewisePolynomial.h`
- Represents and evaluates piecewise polynomial functions.

### Point Utilities
**File:** `point.h`
- Structures and utilities for geometric point.

### Spline Interpolation
**File:** `spline.h`
- Provides cubic spline interpolation for generating smooth paths.
- Features include:
  - Natural and clamped boundary conditions.
  - Monotonicity adjustments for realistic curves.

---
