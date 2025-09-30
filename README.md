# Automated Driving Open Research (ADORe)

![ADORe Logo](documentation/landing_page/img/adore_logo_white.png)

## About ADORe
Eclipse ADORe is a modular software library and toolkit for decision making, planning, control and simulation of 
automated vehicles. It is developed by [The German Aerospace Center (DLR), Institute for Transportation Systems 🔗](https://www.dlr.de/ts/en).
 - ADORe is [ROS 2 🔗](https://ros.org) based
 - ADORe is fully containerized using [Docker 🔗](https://docker.io)
  - ADORe is currently deployed on DLR TS institute research vehicles [FASCar 🔗](https://www.dlr.de/en/research-and-transfer/research-infrastructure/fascar-en) and [VIEWCar II🔗](https://www.dlr.de/en/research-and-transfer/research-infrastructure/view-car)
- ADORe is developed with algorithms and data models applied in real automated driving system for motion planning and control
- ADORe features mechanisms for safe interaction with other CAVs, infrastructure, traffic management, interactions with human-driven vehicles, bicyclists, pedestrians

ADORe is designed around both single agent automated driving (SAAD) and multi agent automated driving (MAAD), to allow both individual and cooperative driving behaviors. ADORes features can be seperated into the following categories.

![ADORe Overview](documentation/landing_page/img/adore_categories_overview.svg)

### SAAD

While driving automated for a single agent, for example on a vehicle like the DLR NGC, ADORe utilized the SAAD modules, viewing ADORe SAAD as a black box of inputs and outputs, get a representation as seen below.

![ADORe SAAD](documentation/landing_page/img/adore_saad.svg)

Diving deeper into the ROS2 node structure of ADORe SAAD leads to be the structure seen below. 

![ADORe SAAD Structure](documentation/landing_page/img/adore_saad_structure.svg)


### MAAD

When using ADORe for control of multiple agent in a cooperative environment, ADORe MAAD can calculate trajectories and behaviors for multiple vehicles at once. Viewing ADORe MAAD as a black box of inputs and outputs, it can been show as seen here.

![ADORe MAAD](documentation/landing_page/img/adore_maad.svg)

# Documentation
In order to get started, it is advised to first check system requirements, follow the installation instruction and then
try out the demo scenarios.

- [Github Pages](https://eclipse.github.io/eclipse-adore/adore)
- [Quick Start](documentation/technical_reference_manual/quick_start.md)
- [Getting started](documentation/technical_reference_manual/getting_started/getting_started.md)
- [Technical Reference Manual](https://eclipse-adore.github.io/adore/mkdocs/about_adore/index.html)


## ADORe In Action
Here you can see one of our automated test vehicles being operated by ADORe:
[![ADORe example video 🔗](https://github.com/DLR-TS/adore_support/blob/master/vivre_flythrough_screenshot2.png?raw=true)](https://youtu.be/tlhPDtr4yxg)

[![YouTube Video](https://img.youtube.com/vi/bRZc1iFohCU/0.jpg)](https://www.youtube.com/watch?v=bRZc1iFohCU)

[![YouTube Video](https://img.youtube.com/vi/MANc_xQ_8sI/0.jpg)](https://www.youtube.com/watch?v=MANc_xQ_8sI)

[![YouTube Video](https://img.youtube.com/vi/Aqvd82A40S4/0.jpg)](https://www.youtube.com/watch?v=Aqvd82A40S4)

[![YouTube Video](https://img.youtube.com/vi/IYbv7Y2nt-k/0.jpg)](https://www.youtube.com/watch?v=IYbv7Y2nt-k)

# Example application
The following video shows an automated vehicle controlled by ADORe in an urban setting in Braunschweig, Germany:
[![ADORe example video](https://github.com/DLR-TS/adore_support/blob/master/adore_vivre_video_preview_20221027.png?raw=true)](https://youtu.be/tlhPDtr4yxg)


