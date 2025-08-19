# ADORe ROS2 Model Checker for Vehicle Safety Monitoring in ADORe

A tool for monitoring and verifying safety properties of autonomous vehicles 
using Computation Tree Logic (CTL) model checking. This tool can analyze both 
live ROS2 data streams and offline bag data files to ensure vehicles comply with 
safety requirements.


This tool is a WORK IN PROGRESS and likely has many bugs.

## Features

- **API**: Included REST API/interface for invoking the model checker 
    [Model Checker API Reference](adore_model_checker_api_reference.md)
- **Dual Mode Operation**: Online monitoring of live ROS2 topics and offline analysis of bag files
- **Configurable Safety Properties**: 50+ built-in safety propositions organized into 10 categories
- **Multi-Vehicle Support**: Monitor multiple vehicles simultaneously with individual configurations
- **Flexible Data Sources**: Map any ROS2 topics to safety propositions with field path extraction
- **CTL Model Checking**: Uses formal verification techniques to prove safety properties
- **Extensible Framework**: Easy to add custom safety propositions and evaluation logic
- **Comprehensive Reporting**: Detailed analysis results with statistics and pass/fail status
- **Auto-importing ROS messages**: All defined ROS messages are auto-imported with the `ROSMessageImporter` class 
- **Dictionary Based Topic Subscription**: All subscribed ROS topic messages are converted to dictionaries with the `ROSMarshaller` class 


## Proposition Categories

## Safety Proposition Categories

| Category | Proposition | Implementation Status |
|----------|-------------|------------------------|
| **Basic Safety** | EGO_SPEED | IMPLEMENTED |
|  | NEAR_GOAL | IMPLEMENTED |
|  | SAFE_DISTANCE_X | IMPLEMENTED |
|  | SAFE_DISTANCE_Y | IMPLEMENTED |
|  | DECELERATION | IMPLEMENTED |
|  | IN_COLLISION | NOT IMPLEMENTED |
| **Lane Compliance** | LANE_KEEPING | IMPLEMENTED |
|  | LANE_CHANGE_SAFE | NOT IMPLEMENTED |
|  | ROAD_BOUNDARY_RESPECT | NOT IMPLEMENTED |
|  | WRONG_WAY_DRIVING | NOT IMPLEMENTED |
| **Traffic Rules** | TRAFFIC_LIGHT_COMPLIANCE | NOT IMPLEMENTED |
|  | STOP_SIGN_COMPLIANCE | NOT IMPLEMENTED |
|  | SPEED_LIMIT_COMPLIANCE | NOT IMPLEMENTED |
|  | YIELD_COMPLIANCE | NOT IMPLEMENTED |
|  | TURN_SIGNAL_USAGE | NOT IMPLEMENTED |
| **Dynamic Safety** | TIME_TO_COLLISION | NOT IMPLEMENTED |
|  | EMERGENCY_BRAKING | NOT IMPLEMENTED |
|  | OBSTACLE_AVOIDANCE | NOT IMPLEMENTED |
|  | PEDESTRIAN_SAFETY | NOT IMPLEMENTED |
|  | CYCLIST_SAFETY | NOT IMPLEMENTED |
|  | BLIND_SPOT_MONITORING | NOT IMPLEMENTED |
|  | ACCELERATION_COMPLIANCE | IMPLEMENTED |
|  | DECELERATION_COMPLIANCE | IMPLEMENTED |
| **Behavioral Smoothness** | SMOOTH_ACCELERATION | NOT IMPLEMENTED |
|  | SMOOTH_STEERING | IMPLEMENTED |
|  | SMOOTH_BRAKING | NOT IMPLEMENTED |
|  | COMFORT_ZONE | NOT IMPLEMENTED |
| **Intersection Behavior** | INTERSECTION_APPROACH | NOT IMPLEMENTED |
|  | RIGHT_OF_WAY | NOT IMPLEMENTED |
|  | INTERSECTION_CLEARANCE | NOT IMPLEMENTED |
|  | TURNING_BEHAVIOR | NOT IMPLEMENTED |
| **System Health** | SENSOR_HEALTH | NOT IMPLEMENTED |
|  | LOCALIZATION_ACCURACY | NOT IMPLEMENTED |
|  | COMMUNICATION_STATUS | NOT IMPLEMENTED |
|  | SYSTEM_RESPONSE_TIME | NOT IMPLEMENTED |
|  | PATH_PLANNING_VALIDITY | NOT IMPLEMENTED |
| **Environmental Adaptation** | WEATHER_ADAPTATION | NOT IMPLEMENTED |
|  | VISIBILITY_ADAPTATION | NOT IMPLEMENTED |
|  | ROAD_CONDITION_ADAPTATION | NOT IMPLEMENTED |
|  | TRAFFIC_DENSITY_ADAPTATION | NOT IMPLEMENTED |
| **Mission Efficiency** | ROUTE_OPTIMIZATION | NOT IMPLEMENTED |
|  | FUEL_EFFICIENCY | NOT IMPLEMENTED |
|  | TIME_EFFICIENCY | NOT IMPLEMENTED |
|  | PARKING_BEHAVIOR | NOT IMPLEMENTED |
| **Advanced Maneuvers** | OVERTAKING_SAFETY | NOT IMPLEMENTED |
|  | MERGING_BEHAVIOR | NOT IMPLEMENTED |
|  | ROUNDABOUT_BEHAVIOR | NOT IMPLEMENTED |
|  | CONSTRUCTION_ZONE_BEHAVIOR | NOT IMPLEMENTED |

## Installation

### Prerequisites

- ROS2 (Foxy, Galactic, Humble, or Iron)
- Python 3.8+

## Installing System Requirements
System-level dependencies are listed in the `requirements.system` file, 
with one package name per line. Lines starting with `#` are treated as comments.
For inline comments, everything after the first `#` on a line will be ignored 
by the installation command.

You can install all necessary `apt` packages by running the following command in your terminal:
```bash
sudo apt-get update
grep -v '^#' requirements.system | sed 's/#.*//' | xargs sudo apt-get install -y
```

Installing required Python packages:
```bash
pip3 install -r requirements.pip3
```

### ROS2 Setup
Make sure your ROS2 environment is sourced:
```bash
source /opt/ros/<your-ros-distro>/setup.bash
```

## Quick Start

### 1. Generate Configuration

Create a minimal configuration file:
```bash
python3 adore_model_checker.py --create-minimal-config minimal_config.yaml
```

### 2. Configure Data Sources

Edit the configuration file to map your ROS2 topics:

```yaml
vehicles:
  - id: 0
    proposition_groups:
      basic_safety:
        enabled: true
        description: "Core safety propositions"
    
    propositions:
      EGO_SPEED:
        enabled: true
        atomic_prop: 'speed_safe'
        formula_type: 'always'
        threshold: 30.0
        data_sources:
          vehicle_state:
            topic: '/ego_vehicle/vehicle_state/dynamic'
            field_path: 'vx'
            transform_function: 'abs'
            cache_duration: 0.1
        evaluation_function: 'speed_limit_evaluator'
```

### 3a. Online Monitoring
Monitor a live vehicle for 60 seconds:
```bash
python3 adore_model_checker.py --mode online --config your_config.yaml --vehicle-id 0 --duration 60
```

### 3b. Offline Analysis 
Analyze offline bag data:
```bash
python3 adore_model_checker.py --mode offline --config your_config.yaml --bag-file data.bag
```

## Configuration

The tool uses YAML configuration files to specify:

- Vehicle data source mappings
- Enabled safety proposition groups
- Individual proposition settings with data sources
- Safety parameters and thresholds
- Monitoring frequency and buffer settings

### Example Configuration

```yaml
monitoring:
  monitoring_frequency: 10.0
  buffer_size: 1000
  log_level: INFO
  debug_mode: false

safety_parameters:
  max_speed: 30.0
  safe_distance_lateral: 1.5
  time_to_collision_threshold: 3.0
  goal_reach_distance: 5.0

vehicles:
  - id: 0
    proposition_groups:
      basic_safety:
        enabled: true
        description: "Core safety propositions"
      dynamic_safety:
        enabled: true
        description: "Dynamic collision avoidance"
      traffic_rules:
        enabled: false
        description: "Traffic law compliance"
    
    propositions:
      EGO_SPEED:
        enabled: true
        atomic_prop: 'speed_safe'
        formula_type: 'always'
        threshold: 30.0
        data_sources:
          vehicle_state:
            topic: '/ego_vehicle/vehicle_state/dynamic'
            field_path: 'vx'
            transform_function: 'abs'
            cache_duration: 0.1
        evaluation_function: 'speed_limit_evaluator'

      NEAR_GOAL:
        enabled: true
        atomic_prop: 'goal_reached'
        formula_type: 'eventually'
        threshold: 5.0
        data_sources:
          route:
            topic: '/ego_vehicle/route'
            field_path: ''
            cache_duration: 5.0
          vehicle_state:
            topic: '/ego_vehicle/vehicle_state/dynamic'
            field_path: ''
            cache_duration: 0.1
        evaluation_function: 'near_goal_evaluator'

      SAFE_DISTANCE_X:
        enabled: false
        atomic_prop: 'longitudinal_safe'
        formula_type: 'always'
        data_sources:
          ego_state:
            topic: '/ego_vehicle/vehicle_state/dynamic'
            field_path: ''
            cache_duration: 0.1
          traffic_participants:
            topic: '/ego_vehicle/traffic_participants'
            field_path: 'data'
            cache_duration: 0.1
        evaluation_function: 'longitudinal_safety_evaluator'
```

### Data Source Configuration

Each proposition can specify multiple data sources:

- **topic**: ROS2 topic name
- **field_path**: Dot-notation path to extract specific fields (empty for full message)
- **data_type**: Optional data type specification
- **transform_function**: Optional data transformation ('abs', 'speed_from_components', etc.)
- **cache_duration**: How long to cache data in seconds

## Formula Types Reference

| Formula Type | CTL Expression | Description | Use Case |
|--------------|----------------|-------------|----------|
| `always` | `A(G(p))` | Property must always hold | Safety invariants |
| `eventually` | `A(F(p))` | Property must eventually hold | Goal reaching |
| `never` | `A(G(¬p))` | Property must never hold | Collision avoidance |
| `always_not` | `A(G(¬p))` | Same as never | Safety violations |
| `next` | `A(X(p))` | Property holds in next state | State transitions |
| `until` | `A(p U q)` | p holds until q becomes true | Conditional behavior |
| `weak_until` | `A(p W q)` | p holds until q or forever | Optional conditions |

## Usage Examples

### Monitor with Debug Output

```bash
python3 adore_model_checker.py --mode online --config config.yaml --vehicle-id 0 --duration 30 --debug
```

### Monitor and Log 
Monitor and log results to a json file:
```bash
python3 adore_model_checker.py --mode online --config config.yaml --vehicle-id 0 --output results.json
```

### Debug Mode with Data Recording
```bash
python3 adore_model_checker.py --mode online --config config.yaml --vehicle-id 0 --debug-mode --data-file recorded_data.yaml
```

### Analyze Recorded Data
```bash
python3 adore_model_checker.py --mode offline --config config.yaml --data-file recorded_data.yaml
```

## Command Line Options

```
usage: adore_model_checker.py [-h] --mode {online,offline} --config CONFIG
                       [--bag-file BAG_FILE] [--vehicle-id VEHICLE_ID]
                       [--duration DURATION] [--output OUTPUT]
                       [--create-minimal-config CREATE_MINIMAL_CONFIG]
                       [--debug]

options:
  -h, --help            show this help message and exit
  --mode {online,offline}
                        Monitoring mode
  --config CONFIG       Configuration file path
  --bag-file BAG_FILE   ROS bag file for offline mode
  --vehicle-id VEHICLE_ID
                        Vehicle ID to monitor (online mode)
  --duration DURATION   Monitoring duration in seconds (online mode)
  --output OUTPUT       Output file for results
  --create-minimal-config CREATE_MINIMAL_CONFIG
                        Create minimal sample config file
  --debug               Enable debug logging
```

## Output Format

The tool provides detailed results with statistics:

```json
{
  "SUMMARY": {
    "total_propositions": 2,
    "analyzed": 2,
    "passed": 1,
    "failed": 1,
    "success_rate": 0.5,
    "overall_result": "FAIL"
  },
  "EGO_SPEED": {
    "result": true,
    "status": "PASS",
    "states_analyzed": 49,
    "kripke_states": 49,
    "statistics": {
      "max_velocity": 3.34,
      "average_velocity": 3.03,
      "speed_threshold": 13.89,
      "states_with_data": 34,
      "states_without_data": 15
    }
  },
  "NEAR_GOAL": {
    "result": false,
    "status": "FAIL",
    "states_analyzed": 49,
    "kripke_states": 49,
    "statistics": {
      "goal_position": {"x": 606447.62, "y": 5797244.84},
      "final_vehicle_position": {"x": 606481.58, "y": 5797319.95},
      "min_distance_to_goal": 82.43,
      "final_distance_to_goal": 82.43,
      "goal_threshold": 5.0
    }
  }
}
```

## Extending the Tool

### Adding Custom Propositions

1. Add new proposition types to `PropositionType` enum with appropriate group
2. Implement evaluation logic in `PropositionEvaluators` class
3. Add to default configuration generation
4. Configure data sources in YAML

### Custom Evaluation Functions

Create new static methods in `PropositionEvaluators`:

```python
@staticmethod
def custom_evaluator(data: Dict[str, Any], config: PropositionConfig, 
                     safety_params: SafetyParameters) -> Optional[bool]:
    # Custom evaluation logic
    return True  # or False based on your logic
```

### Data Transformations

Add new transform functions in `DataTransforms.apply_transform()`:

```python
elif transform_function == "custom_transform":
    return custom_transformation(data)
```

## Architecture

- **ConfigLoader**: Handles YAML configuration parsing and validation
- **OnlineMonitor**: ROS2 data collection with topic subscriptions
- **ModelChecker**: Core CTL model checking logic with Kripke structure creation
- **PropositionEvaluators**: Safety proposition evaluation functions
- **VehicleMonitorAnalyzer**: Orchestrates analysis and reporting
- **DataTransforms**: Data extraction and transformation utilities

## Dependencies

- **pyModelChecking**: CTL model checking library
- **ROSMarshaller**: ROS2 interface for topic subscription and data handling
- **pandas/numpy**: Data processing and analysis
- **PyYAML**: Configuration file parsing
- **threading/queue**: Concurrent data collection

## Troubleshooting

### Common Issues

1. **ROS2 not found**: Ensure ROS2 is installed and sourced
2. **Topic not found**: Check topic names with `ros2 topic list`
3. **No data for proposition**: Check topic names and field paths in configuration
4. **Missing evaluation function**: Ensure evaluation_function matches available functions
5. **CTL formula errors**: Verify formula_type is supported

### Debug Tips

- Use `--debug` flag for detailed logging
- Check data source configuration with first few states
- Verify topic publication with `ros2 topic echo`
- Use `--debug-mode` to record data for offline analysis

### Performance Considerations

- Adjust `monitoring_frequency` based on system capabilities
- Set appropriate `cache_duration` for different data sources
- Limit `buffer_size` for memory-constrained systems
- Use field_path extraction to reduce data processing overhead


## Example Output
The following section shows exaple terminal and report output from the model 
checker.


Running the following command while running the `simulation_scenario.py` scenario
yields the following console output:
Command:
```bash
python3 adore_model_checker.py --mode online --config adore_safety_checks.yaml --vehicle-id 0 --duration 5 --output adore_safety_checks.json
```
Console Output:
```text
Starting online monitoring for vehicle 0 for 5.0 seconds...
ROS command: ros2 topic echo /ego_vehicle/vehicle_state/dynamic
Subscription thread started for topic: /ego_vehicle/vehicle_state/dynamic
Started process for /ego_vehicle/vehicle_state/dynamic (PID: 1464101)
ROS command: ros2 topic echo /ego_vehicle/route
Subscription thread started for topic: /ego_vehicle/route
Started process for /ego_vehicle/route (PID: 1464142)
============================================================
DYNAMIC VEHICLE MONITORING RESULTS
============================================================

SUMMARY:
  Total Propositions: 2
  Analyzed: 2
  Passed: 2
  Failed: 0
  Success Rate: 100.0%
  Overall Result: PASS

DETAILED RESULTS:
------------------------------------------------------------
  EGO_SPEED                      : PASS     (49 states, 49 Kripke states)
                                     Max velocity: 0.00 m/s, Avg velocity: 0.00 m/s
                                     Speed threshold: 13.89 m/s
                                     States with data: 44, without data: 5
                                     Valid evaluations: 49, failed evaluations: 0
  NEAR_GOAL                      : PASS     (49 states, 38 Kripke states)
                                     Goal position: (606447.62, 5797244.84)
                                     Final vehicle position: (606446.25, 5797247.34)
                                     Min distance to goal: 2.85m
                                     Final distance to goal: 2.85m
                                     Distance threshold: 5.00m
                                     States with data: 0, without data: 11

Results saved to: adore_safety_checks.json
```
Generated json Report:
```json
{
  "EGO_SPEED": {
    "result": true,
    "status": "PASS",
    "states_analyzed": 49,
    "kripke_states": 49,
    "statistics": {
      "max_velocity": 0.002271388617618119,
      "average_velocity": 0.002271388617618121,
      "speed_threshold": 13.89,
      "states_with_data": 44,
      "states_without_data": 5,
      "valid_evaluations": 49,
      "failed_evaluations": 0,
      "true_evaluations": 49,
      "false_evaluations": 0,
      "speed_values": [
        0.002271388617618119,
        0.002271388617618119,
        0.002271388617618119,
        0.002271388617618119,
        0.002271388617618119,
        0.002271388617618119,
        0.002271388617618119,
        0.002271388617618119,
        0.002271388617618119,
        0.002271388617618119,
        0.002271388617618119,
        0.002271388617618119,
        0.002271388617618119,
        0.002271388617618119,
        0.002271388617618119,
        0.002271388617618119,
        0.002271388617618119,
        0.002271388617618119,
        0.002271388617618119,
        0.002271388617618119,
        0.002271388617618119,
        0.002271388617618119,
        0.002271388617618119,
        0.002271388617618119,
        0.002271388617618119,
        0.002271388617618119,
        0.002271388617618119,
        0.002271388617618119,
        0.002271388617618119,
        0.002271388617618119,
        0.002271388617618119,
        0.002271388617618119,
        0.002271388617618119,
        0.002271388617618119,
        0.002271388617618119,
        0.002271388617618119,
        0.002271388617618119,
        0.002271388617618119,
        0.002271388617618119,
        0.002271388617618119,
        0.002271388617618119,
        0.002271388617618119,
        0.002271388617618119,
        0.002271388617618119
      ],
      "speed_sum": 0.09994109917519733
    }
  },
  "NEAR_GOAL": {
    "result": true,
    "status": "PASS",
    "states_analyzed": 49,
    "kripke_states": 38,
    "statistics": {
      "goal_position": {
        "x": 606447.62,
        "y": 5797244.84
      },
      "final_vehicle_position": {
        "x": 606446.2517311152,
        "y": 5797247.336126228
      },
      "min_distance_to_goal": 2.8465427956342575,
      "final_distance_to_goal": 2.8465427956342575,
      "goal_threshold": 5.0,
      "states_with_data": 0,
      "states_without_data": 11,
      "valid_evaluations": 38,
      "failed_evaluations": 0,
      "true_evaluations": 38,
      "false_evaluations": 0
    }
  },
  "SUMMARY": {
    "total_propositions": 2,
    "analyzed": 2,
    "passed": 2,
    "failed": 0,
    "success_rate": 1.0,
    "overall_result": "PASS"
  }
}
```


## Proposition Descriptions 

### ACCELERATION_COMPLIANCE
Monitors the difference between commanded and measured acceleration during acceleration events:
- **Threshold**: Configurable maximum error (default: 1.5 m/s²)
- **Evaluation**: Only active during positive commanded acceleration (> 0.1 m/s²)
- **Statistics**: Max/min/avg errors, compliance rates, violation counts

### DECELERATION_COMPLIANCE  
Monitors the difference between commanded and measured acceleration during deceleration events:
- **Threshold**: Configurable maximum error (default: 2.0 m/s²)
- **Evaluation**: Only active during negative commanded acceleration (< -0.1 m/s²)
- **Statistics**: Max/min/avg errors, compliance rates, violation counts

Both propositions provide detailed statistics including:
- Maximum and average tracking errors
- Measured vs commanded acceleration values
- Compliance violation counts and rates
- Separate event tracking for acceleration vs deceleration


## Building an APT `.deb` package
This project contains a `Makefile` and `Dockerfile`
that can be used to to generate an APT `.deb` package. To generate a package
invoke:
```
make build
```

> ℹ️ **Info:** Requires `Docker` and `GNU Make` to be installed. 

