# ADORe Mission Control

The ADORe Mission Control is a web-based control interface for autonomous 
driving research and development using the ADORe framework.

## Features

### Scenario Management
- **Scenario Selection**: Search and select from available launch files
- **Live Editor**: Python/ROS2 launch file editor with syntax highlighting
- **Loop Mode**: Automatic scenario restart with configurable runtime and delays
- **Real-time Monitoring**: Live status updates and system logs

### Model Checking
- **Online Verification**: Automated safety property verification during scenario execution
- **Results Dashboard**: Visual proposition status with pass/fail indicators
- **Configurable**: Custom config files and verification parameters

### Data Recording
- **ROS2 Bag Recording**: Selective or full topic recording with timestamped files
- **Topic Management**: Real-time topic discovery and selection
- **Storage**: Organized file storage with metadata

### Position Planning
- **Interactive Map**: Click-to-place start/goal markers with route visualization
- **Multi-format Coordinates**: Lat/Long and UTM coordinate systems
- **Code Generation**: Automatic Python position code generation
- **Location Search**: OpenStreetMap integration for location lookup

### Visualization
- **Foxglove Integration**: Embedded real-time data visualization
- **System Monitoring**: Running nodes and process status
- **Log Streaming**: Multi-pane output monitoring

## Interface Layout

- **Scenario Manager**: Main control panel for scenario execution
- **Output**: System logs and model checking results
- **Visualization**: Real-time data plots and system state
- **Goal Picker**: Map-based position planning tool
- **API Reference**: Integrated documentation

## Quick Start

1. Start the ADORe CLI
From the root directory of the ADORe repository run:
```
make cli
```

You will be presented with a prompt:
```
Welcome to the ADORe Development CLI Ubuntu 24.04.2 LTS (GNU/Linux 6.8.0-65-generic x86_64)

            ____ 
         __/  |_\__
        |           -. 
  ......'-(_)---(_)--' 
  Type 'help' for more information.


Sourced ros2_workspace/install/local_setup.zsh environment
ADORe API is running (PID: 413800)
Access at: http://localhost:8888
```

2. Open the web interface specified by the prompt e.g., [http://localhost:8888](http://localhost:8888) 
3. Use **Goal Picker** to set start/goal positions
4. Select or create a scenario in **Scenario Manager**
5. Enable model checking if needed
6. Start scenario execution
7. Monitor progress in **Output** and **Visualization** tabs

The interface automatically manages ROS2 processes, coordinates between 
components, and provides comprehensive monitoring for autonomous vehicle 
scenario testing.
