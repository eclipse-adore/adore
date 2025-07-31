# ADORe API Reference

Overview

The ADORe API provides comprehensive control over scenario management, model checking, bag recording, and ROS2 system integration. All endpoints return JSON responses with appropriate HTTP status codes.

## Scenario Management

### Start Scenario

**POST** `/api/scenario/start`

Start a scenario using either a file path or launch file content.

**Request Body:**
```json
{
  "scenario": "path/to/scenario.launch.py" | "launch file content",
  "is_file": true | false
}
```

**Response:**
```json
{
  "success": true,
  "message": "Scenario started successfully"
}
```

### Stop Scenario

**POST** `/api/scenario/stop`

Stop the currently running scenario.

**Response:**
```json
{
  "success": true,
  "message": "Scenario stopped"
}
```

### Restart Scenario

**POST** `/api/scenario/restart`

Restart the current scenario (halts all processes first, then restarts).

**Response:**
```json
{
  "success": true,
  "message": "Scenario restarted successfully"
}
```

### Halt All Scenarios

**POST** `/api/scenario/halt`

Halt all running scenarios and ROS2 processes.

**Response:**
```json
{
  "success": true,
  "message": "All scenarios halted"
}
```

### Get Scenario Output

**GET** `/api/scenario/output?lines=1000`

Get stdout/stderr output from the running scenario.

**Query Parameters:**
- `lines`: number of lines to return (default: 1000)

**Response:**
```json
{
  "output": "scenario output text..."
}
```

### Get Scenario Status

**GET** `/api/scenario/status`

Get current scenario status and details.

**Response:**
```json
{
  "status": "running" | "idle" | "failed",
  "scenario": "current_scenario_name",
  "scenario_content": "launch file content",
  "loop_mode": true | false,
  "loop_delay": 0,
  "default_runtime": 60,
  "runtime": 45.2,
  "pid": 12345
}
```

### Get Available Scenarios

**GET** `/api/scenario/get`

Get list of available scenario files.

**Response:**
```json
{
  "scenarios": ["scenario1.launch.py", "scenario2.launch.py"]
}
```

### Get Scenario Content

**GET** `/api/scenario/content/&lt;path:scenario_path&gt;`

Get the content of a specific scenario file.

**Response:**
```json
{
  "success": true,
  "content": "scenario file content...",
  "path": "scenario1.launch.py"
}
```

### Save Scenario

**POST** `/api/scenario/save`

Save a new scenario file.

**Request Body:**
```json
{
  "name": "my_scenario.launch.py",
  "content": "scenario content..."
}
```

**Response:**
```json
{
  "success": true,
  "message": "Scenario saved as my_scenario.launch.py"
}
```

### Set Loop Mode

**POST** `/api/scenario/loop`

Configure loop mode for automatic scenario restarts.

**Request Body:**
```json
{
  "enabled": true,
  "delay": 5,
  "runtime": 60
}
```

**Response:**
```json
{
  "success": true,
  "message": "Loop mode enabled"
}
```

## Model Checking Management

### Start Online Model Checking

**POST** `/api/model_check/online`

Start online model checking session monitoring live ROS2 data.

**Request Body:**
```json
{
  "config_file": "config/default.yaml",
  "duration": 60.0,
  "vehicle_id": 0
}
```

**Response:**
```json
{
  "run_id": 12345,
  "message": "Model checking started successfully"
}
```

### Get Model Check Results

**GET** `/api/model_check/result/&#x5b;run_id&#x5d;`

Get results of a specific model checking run.

**Response:**
```json
{
  "run_id": 12345,
  "status": "completed" | "running" | "failed" | "cancelled",
  "mode": "online",
  "results": {
    "SUMMARY": {
      "total_propositions": 10,
      "passed": 8,
      "failed": 2,
      "success_rate": 0.8,
      "overall_result": "PASS"
    },
    "proposition_name": {
      "status": "pass" | "fail",
      "description": {...},
      "formula_description": "...",
      "result": 0.95
    }
  },
  "stdout": "model checking output..."
}
```

### Cancel Model Check

**POST** `/api/model_check/cancel/&lt;run_id&gt;`

Cancel a running model checking job.

**Response:**
```json
{
  "message": "Model checking cancelled successfully"
}
```

### Download Model Check Results

**GET** `/api/model_check/result/<run_id>/download`

Download model checking results as JSON file.

## Bag Recording Management

### Start Bag Recording

**POST** `/api/bag/start`

Start bag recording with optional duration and topic selection.

**Request Body:**
```json
{
  "duration": 60,
  "topics": ["/topic1", "/topic2"]
}
```

**Response:**
```json
{
  "success": true,
  "message": "Recording started: scenario_20250721T143022Z",
  "bag_name": "scenario_20250721T143022Z",
  "bag_path": "/full/path/to/bag",
  "topics": ["/topic1", "/topic2"],
  "duration": 60
}
```

### Stop Bag Recording

**POST** `/api/bag/stop`

Stop the currently running bag recording.

**Response:**
```json
{
  "success": true,
  "message": "Recording stopped: scenario_20250721T143022Z",
  "bag_name": "scenario_20250721T143022Z",
  "relative_path": "bag_file_recordings/scenario_20250721T143022Z"
}
```

### Get Bag Recording Status

**GET** `/api/bag/status`

Get current bag recording status.

**Response:**
```json
{
  "status": "idle" | "recording" | "stopped" | "completed" | "failed",
  "bag_name": "scenario_20250721T143022Z",
  "bag_path": "/full/path/to/bag",
  "topics": ["all"] | ["/topic1", "/topic2"],
  "duration": 60,
  "runtime": 45.2,
  "pid": 12345
}
```

### List Bag Recordings

**GET** `/api/bag/list`

List all recorded bag files.

**Response:**
```json
{
  "success": true,
  "bags": [
    {
      "name": "scenario_20250721T143022Z",
      "path": "/full/path/to/bag",
      "relative_path": "bag_file_recordings/scenario_20250721T143022Z",
      "created": "2025-07-21T14:30:22",
      "size_mb": 125.4
    }
  ]
}
```

### Get Bag Recording Output

**GET** `/api/bag/output?lines=100`

Get stdout/stderr output from the bag recording process.

**Query Parameters:**
- `lines`: number of lines to return (default: 100)

**Response:**
```json
{
  "output": "bag recording output text..."
}
```

## Topic Management

### Subscribe to Topic

**GET** `/api/topic/subscribe?topic=/topic_name&limit=10&wait_timeout=1.0`

Subscribe to a ROS2 topic and get recent messages.

**Query Parameters:**
- `topic`: ROS2 topic name (required)
- `limit`: maximum number of messages to return (default: 10)
- `wait_timeout`: time to wait for messages if new subscriber (default: 1.0 seconds)

**Response:**
```json
{
  "success": true,
  "topic": "/topic_name",
  "messages": [
    {
      "timestamp": 1642780800.0,
      "topic": "/topic_name",
      "datatype": "std_msgs/msg/String",
      "data": {"data": "hello world"}
    }
  ],
  "count": 1,
  "new_subscriber": true,
  "waited": 0.5
}
```

### Publish to Topic

**POST** `/api/topic/publish`

Publish a message to a ROS2 topic.

**Request Body:**
```json
{
  "topic": "/topic_name",
  "data": {"data": "hello world"},
  "datatype": "std_msgs/msg/String"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Message published to /topic_name",
  "topic": "/topic_name",
  "datatype": "std_msgs/msg/String"
}
```

### List Active Topics

**GET** `/api/topic/list`

List all active ROS topics in the system and those being managed by the API.

**Response:**
```json
{
  "success": true,
  "managed_topics": {
    "active_subscribers": 2,
    "active_publishers": 1,
    "subscriber_topics": ["/topic1", "/topic2"],
    "publisher_topics": ["/topic3"],
    "ros_available": true
  },
  "system_topics": ["/rosout", "/parameter_events", "/cmd_vel", "/scan"]
}
```

### Get Topic Information

**GET** `/api/topic/info/&lt;path:topic_name&gt;`

Get detailed information about a specific ROS2 topic.

**Response:**
```json
{
  "success": true,
  "topic": "/topic_name",
  "datatype": "std_msgs/msg/String",
  "managed": true
}
```

## Position Management

### Get Stored Positions

**GET** `/api/positions/get`

Get stored start and goal positions from the goal picker.

**Response:**
```json
{
  "start": {
    "lat": 52.5200,
    "lng": 13.4050,
    "utm": {
      "easting": 606372,
      "northing": 5797172,
      "zone": 32,
      "hemisphere": "N"
    }
  },
  "goal": {
    "lat": 52.5300,
    "lng": 13.4150,
    "utm": {
      "easting": 606380,
      "northing": 5797058,
      "zone": 32,
      "hemisphere": "N"
    }
  }
}
```

### Set Positions

**POST** `/api/positions/set`

Store start and/or goal positions.

**Request Body:**
```json
{
  "start": {"lat": 52.5200, "lng": 13.4050},
  "goal": {"lat": 52.5300, "lng": 13.4150}
}
```

**Response:**
```json
{
  "success": true,
  "message": "Positions stored successfully"
}
```

### Clear Positions

**POST** `/api/positions/clear`

Clear all stored positions.

**Response:**
```json
{
  "success": true,
  "message": "Positions cleared"
}
```

## ROS2 System Information

### Get ROS2 Nodes

**GET** `/api/ros2/nodes`

Get cached information about all ROS2 nodes.

**Response:**
```json
{
  "nodes": {
    "/node_name": {
      "name": "/node_name",
      "topics": [...],
      "services": [...],
      "actions": [...]
    }
  },
  "count": 5,
  "last_updated": 1642780800.0
}
```

### Get Running Nodes

**GET** `/api/ros2/nodes/running`

Get list of currently running ROS2 node names.

**Response:**
```json
{
  "running_nodes": ["/node1", "/node2", "/node3"],
  "count": 3
}
```

### Get Node Information

**GET** `/api/ros2/nodes/&lt;node_name&gt;`

Get detailed information about a specific ROS2 node.

**Response:**
```json
{
  "name": "/node_name",
  "topics": [
    {
      "topic": "/topic_name",
      "datatype": "std_msgs/msg/String",
      "role": "publisher" | "subscriber"
    }
  ],
  "services": [...],
  "actions": [...]
}
```

### Get ROS2 Topics

**GET** `/api/ros2/topics`

Get information about all ROS2 topics.

**Response:**
```json
{
  "topics": {
    "/topic_name": {
      "name": "/topic_name",
      "datatype": "std_msgs/msg/String",
      "publishers": ["/node1"],
      "subscribers": ["/node2", "/node3"]
    }
  },
  "count": 10,
  "last_updated": 1642780800.0
}
```

### Get Topic Information

**GET** `/api/ros2/topics/&lt;topic_name&gt;`

Get detailed information about a specific ROS2 topic.

**Response:**
```json
{
  "name": "/topic_name",
  "datatype": "std_msgs/msg/String",
  "publishers": ["/node1"],
  "subscribers": ["/node2", "/node3"]
}
```

### Get ROS2 Datatypes

**GET** `/api/ros2/datatypes`

Get information about all ROS2 message datatypes.

**Response:**
```json
{
  "datatypes": {
    "std_msgs/msg/String": {
      "name": "std_msgs/msg/String",
      "interface_text": "string data",
      "interface": [...],
      "topics": ["/topic1", "/topic2"]
    }
  },
  "count": 25,
  "last_updated": 1642780800.0
}
```

### Get Datatype Information

**GET** `/api/ros2/datatypes/&lt;datatype_name&gt;`

Get detailed information about a specific ROS2 datatype.

**Response:**
```json
{
  "name": "std_msgs/msg/String",
  "interface_text": "string data",
  "interface": [...],
  "topics": ["/topic1", "/topic2"]
}
```

### Get ROS2 Graph

**GET** `/api/ros2/graph`

Get ROS2 computation graph data.

**Response:**
```json
{
  "graph": {
    "nodes": [...],
    "edges": [...],
    "metadata": {...}
  },
  "last_updated": 1642780800.0
}
```

### Get ROS2 Status

**GET** `/api/ros2/status`

Get ROS2 API worker status and cache statistics.

**Response:**
```json
{
  "worker_running": true,
  "last_updated": {
    "nodes": 1642780800.0,
    "topics": 1642780801.0,
    "datatypes": 1642780802.0
  },
  "cache_stats": {
    "nodes": 5,
    "topics": 10,
    "datatypes": 25
  }
}
```

### Refresh ROS2 Cache

**POST** `/api/ros2/refresh`

Force refresh of ROS2 system cache.

**Response:**
```json
{
  "message": "Cache refreshed successfully"
}
```

## System Status

### Get API Status

**GET** `/api/status`

Get overall API status and feature availability.

**Response:**
```json
{
  "adore_api": "running",
  "model_checker_available": true,
  "ros_marshaller_available": true,
  "bag_recording_available": true
}
```

## Error Handling

All endpoints return appropriate HTTP status codes:

- **200 OK**: Successful operation
- **400 Bad Request**: Invalid request parameters or body
- **404 Not Found**: Resource not found
- **500 Internal Server Error**: Server error

Error responses include a descriptive message:

```json
{
  "success": false,
  "message": "Error description"
}
```
