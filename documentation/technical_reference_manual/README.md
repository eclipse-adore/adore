# Automated Driving Open Research (ADORe)
Eclipse ADORe is a [ROS 2 🔗](https://ros.org/) based modular software library and toolkit for decision making, planning, control and simulation of automated vehicles. 
ADORe provides:

- Algorithms and data models applied in real automated driving system for motion planning and control
- Mechanisms for safe interaction with other CAVs, infrastructure, traffic management, interactions with human-driven vehicles, bicyclists, pedestrians
- Integration with typical tools and formats such as ROS 2, [SUMO](https://github.com/eclipse/sumo), CARLA, OpenDrive, Road2Simulation, ITS-G5 V2X (MAPEM, SPATEM, DENM, MCM, SREM)

# Overview
An ADORe control system works in concert with a perception stack (not provided) to control an autonomous vehicle platform.
Using V2X radio messages, a list of detected objects and ego vehicle position and velocity, the ADORe control system provides control inputs to a vehicle platform in order to steer it along a given high-definition roadmap to the desired goal location.
![ADORe architectural overview](https://github.com/DLR-TS/adore_support/blob/master/documentation/adore_overview_v03_20221027.png?raw=true)

# Example application
The following video shows an automated vehicle controlled by ADORe in an urban setting in Braunschweig, Germany:
[![ADORe example video](https://github.com/DLR-TS/adore_support/blob/master/adore_vivre_video_preview_20221027.png?raw=true)](https://youtu.be/tlhPDtr4yxg)

## ADORe In Action
Here you can see one of our automated test vehicles being operated by ADORe:
[![ADORe example video 🔗](https://github.com/DLR-TS/adore_support/blob/master/vivre_flythrough_screenshot2.png?raw=true)](https://youtu.be/tlhPDtr4yxg)

# Next Steps
In order to get started, it is advised to first check system requirements, follow the installation instruction and then try out the demo scenarios.

- [System Requirements](getting_started/system_requirements.md)
- [Installation and getting started](getting_started/getting_started.md)
- [Technical Reference Manual](technical_documentation)
- [Troubleshooting]()
- [How to contribute](CONTRIBUTING.md)



