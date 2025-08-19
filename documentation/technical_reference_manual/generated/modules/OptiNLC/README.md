# OptiNLC 
A C++ library implementing Sequential Quadratic Programming
With a docker build and run environment

OptiNLC (Optimization of Non-Linear Control) is an open-source toolbox designed for solving optimization control problems. This documentation provides an overview of optimization problems, optimization control problems, and a guide on how to use the OptiNLC toolbox.


## Getting Started
Docker and make required to package and build OptiNLC

1. Clone the repo
2. Clone the submodules
```bash
git submodule update --init --recursive
```

## Running the example program
```bash
make run
```

## Running unit tests 
```bash
make test
```

# OptiNLC Toolbox Documentation

## Introduction

OptiNLC (Optimization of Non-Linear Control) is an open-source toolbox designed for solving optimization control problems. This documentation provides an overview of optimization problems, optimization control problems, and a guide on how to use the OptiNLC toolbox.

## Optimization Problem

An optimization problem involves finding the best solution from a set of feasible solutions. It consists of an objective function to be minimized or maximized, subject to a set of constraints. The goal is to identify the input values that result in the optimal value of the objective function.

## Optimization Control Problem

Optimization control problems extend the concept of optimization to dynamic systems. In these problems, the goal is to find the optimal control inputs over a given time horizon to drive a dynamic system to an optimal state while satisfying constraints.

## OptiNLC Toolbox

The OptiNLC toolbox is designed to handle optimization control problems efficiently. Below is an example template demonstrating the usage of the toolbox.

```cpp
// ... (Same code as provided in the previous response)
