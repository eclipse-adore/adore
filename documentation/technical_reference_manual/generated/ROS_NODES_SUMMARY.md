# ROS Nodes Summary
This document summarizes all of the ROS nodes in ADORe, always review each README.md for the complete documentation for a given node.
all ROS nodes are located in `ros2_workspace/src`

## Package: simulated_remote_operator
- Node: simulated_remote_operator
- Location: simulated_remote_operator
- Summary: # Simulated Remote Operator ROS2 python node that creates a GUI that simulated the actions available to a remote operator.

## Package: ros2_syslog
- Node: ros2_syslog
- Location: ros2_syslog
- Summary: # ros2_syslog The ros2_syslog node/program subscribes to ROS2 messages of type `telemetry` and writes them to the syslog. The syslog is rate limited. This is defined by a global variable `MAX_MESSAGES_PER_SECOND` Syslog messages are automatically forward by rsyslog as telemetry if configured by the host. 1. Build the package with: ```bash bash build.sh ``` 2. Run the node: ```bash bash run.sh ```

## Package: simulated_vehicle
- Node: simulated_vehicle
- Location: simulated_vehicle
- Summary: # Simulated Vehicle Node

## Package: cpp_publisher_subscriber_template
- Node: cpp_publisher_subscriber_template
- Location: example_nodes/cpp_publisher_subscriber_template
- Summary: # C++ Publisher Subscriber Template This project provides a minimal c++ publisher and subscriber example. This node can be used as a template to create another node.

## Package: ros2_eigen_hello_world
- Node: ros2_eigen_hello_world
- Location: example_nodes/ros2_eigen_hello_world
- Summary: # ros2_eigen_hello_world This is a minimal ROS2 hello world program that uses the Eigen3 library 1. Build the package with: ```bash bash build.sh ``` 2. Run the node: ```bash bash run.sh ``` You should get the following output: ``` [INFO] [1700066229.388250475] [ros2_eigen_hello_world]: ROS2 Eigen3 Hello, World! [INFO] [1700066229.388365706] [ros2_eigen_hello_world]: m_eigen matrix: 3 -1 2.5 1.5 ```

## Package: ros2_python_hello_world
- Node: ros2_python_hello_world
- Location: example_nodes/ros2_python_hello_world
- Summary: # ROS2 Python Node Template This is a ros2 hello world python template for creating ROS2 Python packages with proper executable entry points that work with `ros2 run`.

## Package: ros2_hello_world
- Node: ros2_hello_world
- Location: example_nodes/ros2_hello_world
- Summary: # ros2_hello_world This is a minimal ROS2 Hello, World program incorporating a GNU Makefile and unit tests with gunit. This node/program provides a GNU Makefile for building, testing, and running. Use this node as a template for creating new c++ nodes. 1. Build the package with: ```bash make build ``` 2. Test the node: ```bash make test ``` 3. Run the node: ```bash make run ```

## Package: adore_dynamics_conversions
- Node: adore_dynamics_conversions
- Location: conversions/adore_dynamics_conversions

## Package: adore_map_conversions
- Node: adore_map_conversions
- Location: conversions/adore_map_conversions

## Package: adore_math_conversions
- Node: adore_math_conversions
- Location: conversions/adore_math_conversions

## Package: carla_msgs
- Node: ros-carla-msgs
- Location: ros2_messages/ros-carla-msgs
- Summary: # ros-carla-msgs Official ROS messages for CARLA. Use them in conjunction with [CARLA ROS bridge](https://github.com/carla-simulator/ros-bridge).

## Package: adore_ros2_msgs
- Node: adore_ros2_msgs
- Location: ros2_messages/adore_ros2_msgs
- Summary: # ADORe ROS2 Messages

## Package: simulated_infrastructure
- Node: simulated_infrastructure
- Location: simulated_infrastructure
- Summary: # Simulated Infrastructure

## Package: trajectory_tracker
- Node: trajectory_tracker
- Location: trajectory_tracker
- Summary: # Trajectory Tracker Node

## Package: mission_control
- Node: mission_control
- Location: mission_control
- Summary: # Mission Control Node

## Package: decision_maker_infrastructure
- Node: decision_maker_infrastructure
- Location: decision_maker_infrastructure
- Summary: # decision_maker_infrastructure This node/program provides a multi agent decision maker for the infrastructure. 1. Build the package with: ```bash make build ``` 3. Test the node: ```bash make test ``` 2. Run the node: ```bash make run ```

## Package: decision_maker
- Node: decision_maker
- Location: decision_maker
- Summary: # Decision Maker Node

## Package: visualizer
- Node: visualizer
- Location: visualizer
- Summary: # Visualization Node for Autonomous Systems

## Package: traffic_predictor
- Node: traffic_predictor
- Location: traffic_predictor
- Summary: # traffic predictor This is a traffic prediction node that takes a description of the state of each vehicle, including position and velocity. and outputs a navigation message vector of points representing the center of the lane in the direction of the navigation goal. This node/program provides a GNU Makefile for building, testing, and running. 1. Build the package with (within the ADORe CLI): ```bash cd ros2_workspace/src/traffic_predictor make build ``` 2. start a scenario(within the ADORe CLI): ```bash cd adore_scenarios/simuation_scenarios ros2 launch adso_demo_1.py ``` or ```bash cd adore_scenarios/simuation_scenarios ros2 launch adso_demo_2.py ``` 3. Run the node(within the ADORe CLI): ```bash cd ros2_workspace/src/traffic_predictor make run ``` 4. In another scenario the output can be observed(within the ADORe CLI): ```bash ros2 topic echo /ego_vehicle/traffic_prediction ```

## Package: sumo_bridge
- Node: sumo_bridge
- Location: interfaces/sumo_bridge
- Summary: <!-- ******************************************************************************** * Copyright (C) 2017-2025 German Aerospace Center (DLR). * Eclipse ADORe, Automated Driving Open Research https://eclipse.org/adore * * This program and the accompanying materials are made available under the * terms of the Eclipse Public License 2.0 which is available at * http://www.eclipse.org/legal/epl-2.0. * * SPDX-License-Identifier: EPL-2.0 * * Contributors: * Matthias Nichting ******************************************************************************** --> # SUMO bridge This package contains ROS2 nodes to convert and exchange data between ADORe ROS2 and SUMO (version 1.22.0) and ADORe. It allows to control an ADORe vehicle in SUMO.

## Package: carla_bridge
- Node: carla_bridge
- Location: interfaces/carla_bridge
- Summary: <!-- /******************************************************************************** * Copyright (C) 2017-2025 German Aerospace Center (DLR). * Eclipse ADORe, Automated Driving Open Research https://eclipse.org/adore * * This program and the accompanying materials are made available under the * terms of the Eclipse Public License 2.0 which is available at * http://www.eclipse.org/legal/epl-2.0. * * SPDX-License-Identifier: EPL-2.0 * * Contributors: * Matthias Nichting ********************************************************************************/ --> # ADORe CARLA bridge This package contains ROS2 nodes to convert and exchange data between the native ROS2 interface of CARLA (version 0.10.0) and ADORe. It allows to control a vehicle with ADORe inside the CARLA simulation. Note: The ADORe CARLA bridge is experimental.

