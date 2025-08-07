# ADORe API

REST API for autonomous driving scenario management, model checking, data recording, and ROS2 system integration.

## Quick Start

```bash
# Start the API server
python adore_api.py

# Check status
curl http://localhost:5000/api/status
```

## Documentation

- **[📖 API Reference](api_reference.md)** - Complete endpoint documentation with request/response schemas
- **[💻 cURL Examples](api_reference_curl_examples.md)** - Ready-to-use command examples for all endpoints

## Key Features

- **Scenario Management** - Start, stop, restart ROS2 launch scenarios
- **Model Checking** - Online safety verification with CTL model checker
- **Data Recording** - ROS bag recording with topic selection
- **ROS2 Integration** - Real-time topic subscription and publishing
- **Position Management** - Goal picker integration with coordinate conversion

## Web Interface

Access the ADORe Mission Control interface at `http://localhost:5000` for a complete web-based dashboard.

## Base URL

```
http://localhost:5000/api
```
