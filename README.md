# Automated Driving Open Research (ADORe)

## About ADORe
Eclipse ADORe is a modular software library and toolkit for decision making, planning, control and simulation of 
automated vehicles. It is developed by [The German Aerospace Center (DLR), 
 Institute for Transportation Systems 🔗](https://www.dlr.de/ts/en).

ADORe provides some of the following features and capabilities:
- Algorithms and data models applied in real automated driving system for 
motion planning and control
- Mechanisms for safe interaction with other CAVs, infrastructure, traffic 
management, interactions with human-driven vehicles, bicyclists, pedestrians
 - ADORe is [ROS 2 🔗](https://ros.org) based
 - ADORe is fully containerized using [Docker 🔗](https://docker.io)
 - ADORe has a REST API for managing scenarios(start, stop restart) 
 - ADORe is currently deployed on DLR TS institute research vehicles [FASCar 🔗](https://www.dlr.de/en/research-and-transfer/research-infrastructure/fascar-en) and [VIEWCar II🔗](https://www.dlr.de/en/research-and-transfer/research-infrastructure/view-car)

An ADORe control system works in concert with a perception stack (not provided) to control an autonomous vehicle 
platform.
Using V2X radio messages, a list of detected objects and ego vehicle position and velocity, the ADORe control system 
provides control inputs to a vehicle platform in order to steer it along a given high-definition roadmap to the desired
goal location.
![ADORe architectural overview](https://github.com/DLR-TS/adore_support/blob/master/documentation/adore_overview_v03_20221027.png?raw=true)

# Key Features


# Documentation
In order to get started, it is advised to first check system requirements, follow the installation instruction and then
try out the demo scenarios.

- [Github Pages](https://eclipse-adore.github.io/adore/)
- [Quick Start](documentation/technical_reference_manual/quick_start.md)
- [Getting started](documentation/technical_reference_manual/getting_started/getting_started.md)
- [Technical Reference Manual](documentation/technical_reference_manual/technical_reference_manual.md)


## ADORe In Action
Here you can see one of our automated test vehicles being operated by ADORe:
[![ADORe example video 🔗](https://github.com/DLR-TS/adore_support/blob/master/vivre_flythrough_screenshot2.png?raw=true)](https://youtu.be/tlhPDtr4yxg)

# Example application
The following video shows an automated vehicle controlled by ADORe in an urban setting in Braunschweig, Germany:
[![ADORe example video](https://github.com/DLR-TS/adore_support/blob/master/adore_vivre_video_preview_20221027.png?raw=true)](https://youtu.be/tlhPDtr4yxg)


