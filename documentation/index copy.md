# ADORe Documentation

Welcome to the documentation for **ADORe** – the Autonomous Driving Open Research platform.

This site is organised into:

- high-level **overview and guides** for users who want to run scenarios and understand the system, and  
- a **developer-focused reference** for working on the C++ libraries, ROS 2 nodes, and tools.

Use the navigation on the left, or jump in from the sections below.

---

## Overview

If you’re new to ADORe, start here:

- 👉 **[What is ADORe?](technical_reference_manual/about_adore.md)**  
  High-level description of the project and its goals.

- 🚀 **[Quick start](technical_reference_manual/quick_start.md)**  
  Short walkthrough to get ADORe running and see your first scenario.

- 📚 **[Publications](technical_reference_manual/publications.md)**  
  Related papers and publications.

- 📬 **[Contact](technical_reference_manual/contact.md)**  
  How to get in touch.

---

## Getting started

More detailed guidance to get your environment ready:

- 📖 **[Getting started guide](technical_reference_manual/getting_started/getting_started.md)**  
  Overall introduction and first steps.

- 🖥️ **[System requirements](technical_reference_manual/getting_started/system_requirements.md)**  
  Hardware and software requirements.

- ✅ **[Prerequisites](technical_reference_manual/getting_started/prerequisites.md)**  
  Dependencies and setup steps you need before running ADORe.

- 🐳 **[Installing Docker](technical_reference_manual/getting_started/installing_docker.md)**  
  How to install and configure Docker for ADORe.

- ▶️ **[Run your first scenario](technical_reference_manual/getting_started/running_your_first_scenario.md)**  
  Step-by-step instructions for running a sample scenario.

---

## Using ADORe

Once ADORe is running, these pages help you work with it day-to-day:

- 💻 **[ADORe CLI](technical_reference_manual/system_and_development/adore_cli.md)**  
  Command line interface and workflows.

- 🌍 **[Scenario generation](technical_reference_manual/system_and_development/scenario_generation.md)**  
  How to create and configure scenarios.

- 🔍 **[Model checking with ADORe Mission Control](technical_reference_manual/system_and_development/model_checking_with_the_adore_mission_control.md)**  
  Using Mission Control for model checking.

- 🛠️ **[Problems and solutions](technical_reference_manual/problems_and_solutions.md)**  
  Common issues and how to fix them.

---

## Development guide

For contributors and core developers working on the codebase:

- 🧱 **[Development overview](technical_reference_manual/system_and_development/system_and_development.md)**  
  Repository structure and main components.

- 🔓 **[Anonymous cloning](technical_reference_manual/system_and_development/anonymous_cloning.md)**  
  Cloning and working with the repo anonymously.

- 🧩 **[Creating a new node](technical_reference_manual/system_and_development/creating_a_new_node.md)**  
  How to add a new ROS 2 node to ADORe.

- 🧪 **[ROS unit testing](technical_reference_manual/system_and_development/ros_unit_testing.md)**  
  Testing individual ROS 2 components.

- 📚 **[C++ library testing](technical_reference_manual/system_and_development/library_testing.md)**  
  How to test the core C++ libraries.

- 🔁 **[System tests](technical_reference_manual/system_and_development/system_tests.md)**  
  End-to-end testing and test stands.

- 🧵 **[Multi-arch support](technical_reference_manual/system_and_development/multiarch_support.md)**  
  Notes on building for different architectures.

- 📄 **[Documentation system](technical_reference_manual/system_and_development/documentation_generation_system.md)**  
  How these docs are generated and how to extend them.

- 📘 **[Doxygen documentation](technical_reference_manual/system_and_development/doxygen_documentation.md)**  
  C++ API documentation generation.

- 📝 **[Documentation overview](technical_reference_manual/system_and_development/documentation.md)**  
  High-level view of the documentation.

- 🎨 **[Docs style guide](technical_reference_manual/styleguide.md)**  
  Conventions for writing and formatting documentation.

---

## Code reference

This section documents the concrete code artefacts: scenarios, libraries, nodes, interfaces, messages, tools, and testing utilities.

### Overview

- 📂 **[Code reference overview](generated/README.md)**

### Scenarios

- 🌐 **[ADORe scenarios](generated/adore_scenarios/README.md)**

### Libraries

Core reusable C++ libraries:

- 📐 **[adore_controllers](generated/adore_libraries/adore_controllers/README.md)**
- 🚗 **[adore_dynamics](generated/adore_libraries/adore_dynamics/README.md)**
- 🗺️ **[adore_map](generated/adore_libraries/adore_map/README.md)**
- 🧮 **[adore_math](generated/adore_libraries/adore_math/README.md)**
- 🧭 **[adore_planning](generated/adore_libraries/adore_planning/README.md)**

### Nodes

ROS 2 nodes that implement system behaviour:

- 🧠 **[decision_maker](generated/adore_ros2_nodes/decision_maker/README.md)**
- 🧩 **[decision_maker_infrastructure](generated/adore_ros2_nodes/decision_maker_infrastructure/README.md)**
- 🎛️ **[mission_control](generated/adore_ros2_nodes/mission_control/README.md)**
- 🕹️ **[simulated_remote_operator](generated/adore_ros2_nodes/simulated_remote_operator/README.md)**
- 🚙 **[simulated_vehicle](generated/adore_ros2_nodes/simulated_vehicle/README.md)**
- 📈 **[trajectory_tracker](generated/adore_ros2_nodes/trajectory_tracker/README.md)**
- 👁️ **[visualizer](generated/adore_ros2_nodes/visualizer/README.md)**

### Interfaces

Bridges to external simulators and tools:

- 🚘 **[CARLA bridge](generated/adore_interfaces/carla_bridge/README.md)**
- 🚦 **[SUMO bridge](generated/adore_interfaces/sumo_bridge/README.md)**

### Conversions

Type conversion and helper packages:

- 🔁 **[adore_dynamics_conversions](generated/adore_ros2_conversions/adore_dynamics_conversions/README.md)**
- 🔁 **[adore_map_conversions](generated/adore_ros2_conversions/adore_map_conversions/README.md)**
- 🔁 **[adore_math_conversions](generated/adore_ros2_conversions/adore_math_conversions/README.md)**

### ROS 2 messages

Message definitions used across the system:

- ✉️ **[adore_ros2_msgs](generated/adore_ros2_msgs/README.md)**
