# Automated Driving Open Research (ADORe)

![ADORe Logo](documentation/technical_reference_manual/img/adore_logo_white.png)

## About ADORe

Eclipse ADORe is a modular software library and toolkit for decision making, planning, control and simulation of 
automated vehicles. It is developed by [The German Aerospace Center (DLR), Institute for Transportation Systems 🔗](https://www.dlr.de/ts/en).
 - ADORe is [ROS 2 🔗](https://ros.org) based
 - ADORe is fully containerized using [Docker 🔗](https://docker.io)
  - ADORe is currently deployed on DLR TS institute research vehicles [FASCar 🔗](https://www.dlr.de/en/research-and-transfer/research-infrastructure/fascar-en) and [VIEWCar II🔗](https://www.dlr.de/en/research-and-transfer/research-infrastructure/view-car)
- ADORe is developed with algorithms and data models applied in real automated driving system for motion planning and control
- ADORe features mechanisms for safe interaction with other CAVs, infrastructure, traffic management, interactions with human-driven vehicles, bicyclists, pedestrians

ADORe is designed around both single agent automated driving (SAAD) and multi agent automated driving (MAAD), to allow both individual and cooperative driving behaviors.

# Documentation
Please see full docs at [Github Pages](https://eclipse-adore.github.io/adore/)

## Getting Started
In order to get started, it is advised to first check system requirements, follow the installation instruction and then
try out the demo scenarios.

This guide will help you get your system set up and configured to run ADORe.

1. First review the [System Requirements 🔗](documentation/technical_reference_manual/getting_started/system_requirements.md). 

2. Next review the [Prerequisites 🔗](documentation/technical_reference_manual/getting_started/prerequisites.md) 

## Cloning the ADORe repository
> **ℹ️INFO:**
> By default this guide assumes you have ssh keys configured for GitHub your GitHub account.
> For help on configuring your ssh keys visit: https://docs.github.com/en/authentication/connecting-to-github-with-ssh/adding-a-new-ssh-key-to-your-github-account


```bash
git clone git@github.com:eclipse-adore/adore.git
cd adore
git submodule update --init --recursive
```

> **⚠️ WARNING:** Failing to update and recursively clone the submodules will result in build failures!

> **ℹ️INFO:** If you would rather clone ADORe anonymously over https please review the [Anonymous Cloning 🔗](documentation/technical_reference_manual/system_and_development/anonymous_cloning.md) guide.

## Building ADORe Developer Environment
> **⚠️ WARNING:**
> To use the ADORe developer environment you must have Docker installed.

To have the easiest entry you can [install just](https://github.com/casey/just)

and run:
```bash
just dev
```

Alternatively, simple call

```bash
.docker/scripts/run_dev.sh
```

This will create and the developer environment where you can build all relevant packages with

```bash
just build
```

The full command list is available with

```bash
just help
```

> **⚠️ WARNING:**
> Building ADORe **will** fail until all submodules have been properly initialized. 
> If cloning or repository initialization fails refer to the
> [troubleshooting](documentation/technical_reference_manual/problems_and_solutions.md) guide before proceeding.
> Do not proceed with building ADORe until `git submodule update --init --receive`
> finishes without error. 

Next proceed to [Running Your First Scenario 🔗](documentation/technical_reference_manual/getting_started/running_your_first_scenario.md) 

## Using in an existing ROS2 project

The ADORe packages adore_(libraries/ros2_conversions/ros2_msgs/ros2_nodes/scenarios) can all be used directly in your existing ros2 project by pasting or symlining them into you ros2/colcon workspace.

# ADORe In Action

### ADORe Road Driving
[![ADORe Along Road Driving Video](documentation/technical_reference_manual/img/driving_road_video_image.png)](https://www.youtube.com/watch?v=bRZc1iFohCU)

### ADORe Remote Operations
[![ADORe Remote Operations Video](documentation/technical_reference_manual/img/remote_operations_video_image.png)](https://www.youtube.com/watch?v=Aqvd82A40S4)

### Simulated Multi-Agent Driving / planning
[![ADORe Simulated MAAD Video](documentation/technical_reference_manual/img/simulated_maad_video_image.png)](https://www.youtube.com/watch?v=IYbv7Y2nt-k)

### ADORe at intelligent intersection
[![YouTube Video](documentation/technical_reference_manual/img/adore_intelligent_intersection_video_image.png)](https://www.youtube.com/watch?v=kDOtkMxxtyM)
