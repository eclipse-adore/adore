# ADORe API Reference - cURL Examples

This document provides comprehensive cURL examples for all ADORe API endpoints.

## Base URL

```bash
export ADORE_API_BASE="http://localhost:5000"
```

## Scenario Management

### Start Scenario (from file)

```bash
curl -X POST "${ADORE_API_BASE}/api/scenario/start" \
  -H "Content-Type: application/json" \
  -d '{
    "scenario": "adore_scenarios/simulation_scenarios/simulation_test.launch.py",
    "is_file": true
  }'
```

### Start Scenario (from content)

```bash
curl -X POST "${ADORE_API_BASE}/api/scenario/start" \
  -H "Content-Type: application/json" \
  -d '{
    "scenario": "from launch import LaunchDescription\ndef generate_launch_description():\n    return LaunchDescription([])",
    "is_file": false
  }'
```

### Stop Scenario

```bash
curl -X POST "${ADORE_API_BASE}/api/scenario/stop"
```

### Restart Scenario

```bash
curl -X POST "${ADORE_API_BASE}/api/scenario/restart"
```

### Halt All Scenarios

```bash
curl -X POST "${ADORE_API_BASE}/api/scenario/halt"
```

### Get Scenario Output

```bash
curl -X GET "${ADORE_API_BASE}/api/scenario/output?lines=100"
```

### Get Scenario Status

```bash
curl -X GET "${ADORE_API_BASE}/api/scenario/status"
```

### Get Available Scenarios

```bash
curl -X GET "${ADORE_API_BASE}/api/scenario/get"
```

### Get Scenario Content

```bash
curl -X GET "${ADORE_API_BASE}/api/scenario/content/scenarios%2Fsimulation_test.launch.py"
```

### Save Scenario

```bash
curl -X POST "${ADORE_API_BASE}/api/scenario/save" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "my_custom_scenario.launch.py",
    "content": "from launch import LaunchDescription\ndef generate_launch_description():\n    return LaunchDescription([])"
  }'
```

### Set Loop Mode

```bash
curl -X POST "${ADORE_API_BASE}/api/scenario/loop" \
  -H "Content-Type: application/json" \
  -d '{
    "enabled": true,
    "delay": 5,
    "runtime": 60
  }'
```

## Model Checking Management

### Start Online Model Checking

```bash
curl -X POST "${ADORE_API_BASE}/api/model_check/online" \
  -H "Content-Type: application/json" \
  -d '{
    "config_file": "config/default.yaml",
    "duration": 60.0,
    "vehicle_id": 0
  }'
```

### Get Model Check Results

```bash
curl -X GET "${ADORE_API_BASE}/api/model_check/result/12345"
```

### Cancel Model Check

```bash
curl -X POST "${ADORE_API_BASE}/api/model_check/cancel/12345"
```

### Download Model Check Results

```bash
curl -X GET "${ADORE_API_BASE}/api/model_check/result/12345/download" \
  -o "model_check_results_12345.json"
```

## Bag Recording Management

### Start Bag Recording (all topics)

```bash
curl -X POST "${ADORE_API_BASE}/api/bag/start" \
  -H "Content-Type: application/json" \
  -d '{
    "duration": 60,
    "topics": []
  }'
```

### Start Bag Recording (specific topics)

```bash
curl -X POST "${ADORE_API_BASE}/api/bag/start" \
  -H "Content-Type: application/json" \
  -d '{
    "duration": 120,
    "topics": ["/cmd_vel", "/scan", "/odom"]
  }'
```

### Stop Bag Recording

```bash
curl -X POST "${ADORE_API_BASE}/api/bag/stop"
```

### Get Bag Recording Status

```bash
curl -X GET "${ADORE_API_BASE}/api/bag/status"
```

### List Bag Recordings

```bash
curl -X GET "${ADORE_API_BASE}/api/bag/list"
```

### Get Bag Recording Output

```bash
curl -X GET "${ADORE_API_BASE}/api/bag/output?lines=50"
```

## Topic Management

### Subscribe to Topic

```bash
curl -X GET "${ADORE_API_BASE}/api/topic/subscribe?topic=/cmd_vel&limit=5&wait_timeout=2.0"
```

### Publish to Topic

```bash
curl -X POST "${ADORE_API_BASE}/api/topic/publish" \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "/cmd_vel",
    "data": {
      "linear": {"x": 1.0, "y": 0.0, "z": 0.0},
      "angular": {"x": 0.0, "y": 0.0, "z": 0.5}
    },
    "datatype": "geometry_msgs/msg/Twist"
  }'
```

### List Active Topics

```bash
curl -X GET "${ADORE_API_BASE}/api/topic/list"
```

### Get Topic Information

```bash
curl -X GET "${ADORE_API_BASE}/api/topic/info/cmd_vel"
```

## Position Management

### Get Stored Positions

```bash
curl -X GET "${ADORE_API_BASE}/api/positions/get"
```

### Set Positions

```bash
curl -X POST "${ADORE_API_BASE}/api/positions/set" \
  -H "Content-Type: application/json" \
  -d '{
    "start": {"lat": 52.314572, "lng": 10.560468},
    "goal": {"lat": 52.314569, "lng": 10.560382}
  }'
```

### Clear Positions

```bash
curl -X POST "${ADORE_API_BASE}/api/positions/clear"
```

## ROS2 System Information

### Get ROS2 Nodes

```bash
curl -X GET "${ADORE_API_BASE}/api/ros2/nodes"
```

### Get Running Nodes

```bash
curl -X GET "${ADORE_API_BASE}/api/ros2/nodes/running"
```

### Get Node Information

```bash
curl -X GET "${ADORE_API_BASE}/api/ros2/nodes/ego_vehicle"
```

### Get ROS2 Topics

```bash
curl -X GET "${ADORE_API_BASE}/api/ros2/topics"
```

### Get Topic Information (ROS2)

```bash
curl -X GET "${ADORE_API_BASE}/api/ros2/topics/cmd_vel"
```

### Get ROS2 Datatypes

```bash
curl -X GET "${ADORE_API_BASE}/api/ros2/datatypes"
```

### Get Datatype Information

```bash
curl -X GET "${ADORE_API_BASE}/api/ros2/datatypes/geometry_msgs%2Fmsg%2FTwist"
```

### Get ROS2 Graph

```bash
curl -X GET "${ADORE_API_BASE}/api/ros2/graph"
```

### Get ROS2 Status

```bash
curl -X GET "${ADORE_API_BASE}/api/ros2/status"
```

### Refresh ROS2 Cache

```bash
curl -X POST "${ADORE_API_BASE}/api/ros2/refresh"
```

## System Status

### Get API Status

```bash
curl -X GET "${ADORE_API_BASE}/api/status"
```

## Common Usage Patterns

### Complete Scenario Workflow

```bash
# 1. Check system status
curl -X GET "${ADORE_API_BASE}/api/status"

# 2. Get available scenarios
curl -X GET "${ADORE_API_BASE}/api/scenario/get"

# 3. Start a scenario with model checking
curl -X POST "${ADORE_API_BASE}/api/scenario/start" \
  -H "Content-Type: application/json" \
  -d '{"scenario": "scenarios/simulation_test.launch.py", "is_file": true}'

# 4. Start model checking
curl -X POST "${ADORE_API_BASE}/api/model_check/online" \
  -H "Content-Type: application/json" \
  -d '{"config_file": "config/default.yaml", "duration": 60.0, "vehicle_id": 0}'

# 5. Start bag recording
curl -X POST "${ADORE_API_BASE}/api/bag/start" \
  -H "Content-Type: application/json" \
  -d '{"duration": 60, "topics": []}'

# 6. Monitor status
curl -X GET "${ADORE_API_BASE}/api/scenario/status"
curl -X GET "${ADORE_API_BASE}/api/bag/status"

# 7. Get results (replace 12345 with actual run_id)
curl -X GET "${ADORE_API_BASE}/api/model_check/result/12345"

# 8. Stop everything
curl -X POST "${ADORE_API_BASE}/api/bag/stop"
curl -X POST "${ADORE_API_BASE}/api/scenario/halt"
```

### Position Management Workflow

```bash
# 1. Set start and goal positions
curl -X POST "${ADORE_API_BASE}/api/positions/set" \
  -H "Content-Type: application/json" \
  -d '{
    "start": {"lat": 52.314572, "lng": 10.560468},
    "goal": {"lat": 52.314569, "lng": 10.560382}
  }'

# 2. Retrieve positions with UTM conversion
curl -X GET "${ADORE_API_BASE}/api/positions/get"

# 3. Clear positions when done
curl -X POST "${ADORE_API_BASE}/api/positions/clear"
```

### ROS2 Topic Interaction

```bash
# 1. List all active topics
curl -X GET "${ADORE_API_BASE}/api/topic/list"

# 2. Subscribe to a topic and get recent messages
curl -X GET "${ADORE_API_BASE}/api/topic/subscribe?topic=/cmd_vel&limit=10"

# 3. Publish a message
curl -X POST "${ADORE_API_BASE}/api/topic/publish" \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "/cmd_vel",
    "data": {"linear": {"x": 0.5, "y": 0.0, "z": 0.0}, "angular": {"x": 0.0, "y": 0.0, "z": 0.1}},
    "datatype": "geometry_msgs/msg/Twist"
  }'

# 4. Get topic information
curl -X GET "${ADORE_API_BASE}/api/topic/info/cmd_vel"
```

## Response Formats

### Success Response
```json
{
  "success": true,
  "message": "Operation completed successfully"
}
```

### Error Response
```json
{
  "success": false,
  "message": "Error description"
}
```
