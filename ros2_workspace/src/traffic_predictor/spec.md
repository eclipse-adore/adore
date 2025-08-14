#### 1. Overview
The Traffic Predictor Node is responsible for predicting future trajectories of
multiple traffic participants using a Multi-Agent planning algorithm. The node 
processes real-time traffic participant data, ego vehicle information, and map 
data to generate trajectory predictions for all vehicles in the scene. The 
system operates with deterministic timing behavior at 10 Hz frequency to ensure
consistent real-time performance.

#### 2. Inputs
- **Traffic Participants Set (10 Hz):**
  - Topic: `ego_vehicle/traffic_participants`
  - Message Type: `adore_ros2_msgs/msg/TrafficParticipantSet`
  - Description: Contains state information for all detected traffic participants including position, velocity, and dynamics.

- **Ego Traffic Participant (10 Hz):**
  - Topic: `ego_vehicle/traffic_participant`  
  - Message Type: `adore_ros2_msgs/msg/TrafficParticipant`
  - Description: State information specific to the ego vehicle.
  - Note: Combined with traffic participants set to form unified input dataset.

- **Local Map Data (10 Hz):**
  - Topic: `ego_vehicle/local_map`
  - Message Type: `adore_ros2_msgs/msg/Map`
  - Description: Local map information including lane geometry, road boundaries, and infrastructure elements.

#### 3. Outputs
- **Traffic Prediction (10 Hz):**
  - Topic: `ego_vehicle/traffic_prediction`
  - Message Type: `adore_ros2_msgs/msg/TrafficParticipantSet`
  - Description: Predicted future trajectories for all traffic participants including the ego vehicle.

#### 4. Constraints
1. **Data Synchronization:**
   - All input data streams (traffic participants, ego vehicle, and map) must be available before processing begins.
   
2. **Real-time Processing:**
   - Trajectory planning must complete within the 100ms time window to maintain 10 Hz output frequency.
   
3. **Multi-Agent Coordination:**
   - Predicted trajectories must account for interactions between all traffic participants.
   
4. **Execution Frequency:**
   - The node must execute at a fixed rate of 10 Hz (100ms intervals).

#### 5. Operational Domain
1. **Traffic Participant Types:**
   - Supports prediction for various vehicle types and dynamic objects detected in the traffic scene.
   
2. **Map Dependencies:**
   - Requires accurate local map data including lane markings, road geometry, and traffic infrastructure.
   
3. **Prediction Horizon:**
   - Generates trajectories for a future time horizon as determined by the Multi-Agent PID planner configuration.
   
4. **Scene Complexity:**
   - Handles multi-vehicle scenarios with varying numbers of traffic participants.

#### 6. Data Types

```json
{
  "node": "/traffic_predictor_node",
  "datatypes": [
    {
      "datatype": "adore_ros2_msgs/msg/TrafficParticipantSet",
      "usage": ["input", "output"],
      "topics": [
        "ego_vehicle/traffic_participants",
        "ego_vehicle/traffic_prediction"
      ],
      "description": "Collection of traffic participants with their states and predicted trajectories",
      "interface_text": "std_msgs/Header header\n\tbuiltin_interfaces/Time stamp\n\t\tint32 sec\n\t\tuint32 nanosec\n\tstring frame_id\nadore_ros2_msgs/TrafficParticipant[] data",
      "interface": [
        {
          "type": "object",
          "datatype": "std_msgs/Header",
          "label": "header",
          "typedef_text": "std_msgs/Header header",
          "fields": [
            {
              "type": "object",
              "datatype": "builtin_interfaces/Time",
              "label": "stamp",
              "typedef_text": "builtin_interfaces/Time stamp",
              "fields": [
                {
                  "type": "primitive",
                  "datatype": "int32",
                  "label": "sec",
                  "typedef_text": "int32 sec"
                },
                {
                  "type": "primitive",
                  "datatype": "uint32", 
                  "label": "nanosec",
                  "typedef_text": "uint32 nanosec"
                }
              ]
            },
            {
              "type": "primitive",
              "datatype": "string",
              "label": "frame_id",
              "typedef_text": "string frame_id"
            }
          ]
        },
        {
          "type": "object_array",
          "datatype": "adore_ros2_msgs/TrafficParticipant",
          "label": "data",
          "typedef_text": "adore_ros2_msgs/TrafficParticipant[] data"
        }
      ]
    },
    {
      "datatype": "adore_ros2_msgs/msg/TrafficParticipant",
      "usage": ["input"],
      "topics": [
        "ego_vehicle/traffic_participant"
      ],
      "description": "Individual traffic participant state including position, velocity, acceleration, and orientation",
      "interface_text": "std_msgs/Header header\n\tbuiltin_interfaces/Time stamp\n\t\tint32 sec\n\t\tuint32 nanosec\n\tstring frame_id\nstring participant_id\nadore_ros2_msgs/VehicleStateDynamic state\n\tfloat64 x\n\tfloat64 y\n\tfloat64 z\n\tfloat64 vx\n\tfloat64 vy\n\tfloat64 yaw_angle\n\tfloat64 yaw_rate\n\tfloat64 steering_angle\n\tfloat64 steering_rate\n\tfloat64 ax\n\tfloat64 ay\n\tfloat64 time\ngeometry_msgs/Polygon shape\n\tgeometry_msgs/Point32[] points\n\t\tfloat32 x\n\t\tfloat32 y\n\t\tfloat32 z\nuint8 classification\nfloat64 confidence",
      "interface": [
        {
          "type": "object",
          "datatype": "std_msgs/Header",
          "label": "header",
          "typedef_text": "std_msgs/Header header"
        },
        {
          "type": "primitive",
          "datatype": "string",
          "label": "participant_id",
          "typedef_text": "string participant_id"
        },
        {
          "type": "object",
          "datatype": "adore_ros2_msgs/VehicleStateDynamic",
          "label": "state",
          "typedef_text": "adore_ros2_msgs/VehicleStateDynamic state",
          "fields": [
            {
              "type": "primitive",
              "datatype": "float64",
              "label": "x",
              "typedef_text": "float64 x"
            },
            {
              "type": "primitive",
              "datatype": "float64",
              "label": "y",
              "typedef_text": "float64 y"
            },
            {
              "type": "primitive",
              "datatype": "float64",
              "label": "z",
              "typedef_text": "float64 z"
            },
            {
              "type": "primitive",
              "datatype": "float64",
              "label": "vx",
              "typedef_text": "float64 vx"
            },
            {
              "type": "primitive",
              "datatype": "float64",
              "label": "vy",
              "typedef_text": "float64 vy"
            },
            {
              "type": "primitive",
              "datatype": "float64",
              "label": "yaw_angle",
              "typedef_text": "float64 yaw_angle"
            },
            {
              "type": "primitive",
              "datatype": "float64",
              "label": "yaw_rate",
              "typedef_text": "float64 yaw_rate"
            },
            {
              "type": "primitive",
              "datatype": "float64",
              "label": "steering_angle",
              "typedef_text": "float64 steering_angle"
            },
            {
              "type": "primitive",
              "datatype": "float64",
              "label": "steering_rate",
              "typedef_text": "float64 steering_rate"
            },
            {
              "type": "primitive",
              "datatype": "float64",
              "label": "ax",
              "typedef_text": "float64 ax"
            },
            {
              "type": "primitive",
              "datatype": "float64",
              "label": "ay",
              "typedef_text": "float64 ay"
            },
            {
              "type": "primitive",
              "datatype": "float64",
              "label": "time",
              "typedef_text": "float64 time"
            }
          ]
        },
        {
          "type": "object",
          "datatype": "geometry_msgs/Polygon",
          "label": "shape",
          "typedef_text": "geometry_msgs/Polygon shape"
        },
        {
          "type": "primitive",
          "datatype": "uint8",
          "label": "classification",
          "typedef_text": "uint8 classification"
        },
        {
          "type": "primitive",
          "datatype": "float64",
          "label": "confidence",
          "typedef_text": "float64 confidence"
        }
      ]
    },
    {
      "datatype": "adore_ros2_msgs/msg/VehicleStateDynamic",
      "usage": ["internal"],
      "topics": [],
      "description": "Dynamic vehicle state information used internally for trajectory calculations",
      "interface_text": "float64 x\nfloat64 y\nfloat64 z\nfloat64 vx\nfloat64 vy\nfloat64 yaw_angle\nfloat64 yaw_rate\nfloat64 steering_angle\nfloat64 steering_rate\nfloat64 ax\nfloat64 ay\nfloat64 time",
      "interface": [
        {
          "type": "primitive",
          "datatype": "float64",
          "label": "x",
          "array_constraint": "",
          "constraint": "",
          "value": "",
          "typedef_text": "float64 x"
        },
        {
          "type": "primitive",
          "datatype": "float64",
          "label": "y",
          "array_constraint": "",
          "constraint": "",
          "value": "",
          "typedef_text": "float64 y"
        },
        {
          "type": "primitive",
          "datatype": "float64",
          "label": "z",
          "array_constraint": "",
          "constraint": "",
          "value": "",
          "typedef_text": "float64 z"
        },
        {
          "type": "primitive",
          "datatype": "float64",
          "label": "vx",
          "array_constraint": "",
          "constraint": "",
          "value": "",
          "typedef_text": "float64 vx"
        },
        {
          "type": "primitive",
          "datatype": "float64",
          "label": "vy",
          "array_constraint": "",
          "constraint": "",
          "value": "",
          "typedef_text": "float64 vy"
        },
        {
          "type": "primitive",
          "datatype": "float64",
          "label": "yaw_angle",
          "array_constraint": "",
          "constraint": "",
          "value": "",
          "typedef_text": "float64 yaw_angle"
        },
        {
          "type": "primitive",
          "datatype": "float64",
          "label": "yaw_rate",
          "array_constraint": "",
          "constraint": "",
          "value": "",
          "typedef_text": "float64 yaw_rate"
        },
        {
          "type": "primitive",
          "datatype": "float64",
          "label": "steering_angle",
          "array_constraint": "",
          "constraint": "",
          "value": "",
          "typedef_text": "float64 steering_angle"
        },
        {
          "type": "primitive",
          "datatype": "float64",
          "label": "steering_rate",
          "array_constraint": "",
          "constraint": "",
          "value": "",
          "typedef_text": "float64 steering_rate"
        },
        {
          "type": "primitive",
          "datatype": "float64",
          "label": "ax",
          "array_constraint": "",
          "constraint": "",
          "value": "",
          "typedef_text": "float64 ax"
        },
        {
          "type": "primitive",
          "datatype": "float64",
          "label": "ay",
          "array_constraint": "",
          "constraint": "",
          "value": "",
          "typedef_text": "float64 ay"
        },
        {
          "type": "primitive",
          "datatype": "float64",
          "label": "time",
          "array_constraint": "",
          "constraint": "",
          "value": "",
          "typedef_text": "float64 time"
        }
      ]
    },
    {
      "datatype": "adore_ros2_msgs/msg/Map",
      "usage": ["input"],
      "topics": [
        "ego_vehicle/local_map"
      ],
      "description": "Local map data containing road geometry, lane information, and infrastructure elements",
      "interface_text": "std_msgs/Header header\n\tbuiltin_interfaces/Time stamp\n\t\tint32 sec\n\t\tuint32 nanosec\n\tstring frame_id\ngeometry_msgs/Polygon boundary\n\tgeometry_msgs/Point32[] points\n\t\tfloat32 x\n\t\tfloat32 y\n\t\tfloat32 z\nfloat64 resolution\nadore_ros2_msgs/LaneElement[] lanes\nadore_ros2_msgs/RoadElement[] road_elements",
      "interface": [
        {
          "type": "object",
          "datatype": "std_msgs/Header",
          "label": "header",
          "typedef_text": "std_msgs/Header header"
        },
        {
          "type": "object",
          "datatype": "geometry_msgs/Polygon",
          "label": "boundary",
          "typedef_text": "geometry_msgs/Polygon boundary"
        },
        {
          "type": "primitive",
          "datatype": "float64",
          "label": "resolution",
          "typedef_text": "float64 resolution"
        },
        {
          "type": "object_array",
          "datatype": "adore_ros2_msgs/LaneElement",
          "label": "lanes",
          "typedef_text": "adore_ros2_msgs/LaneElement[] lanes"
        },
        {
          "type": "object_array",
          "datatype": "adore_ros2_msgs/RoadElement",
          "label": "road_elements",
          "typedef_text": "adore_ros2_msgs/RoadElement[] road_elements"
        }
      ]
    },
    {
      "datatype": "adore_ros2_msgs/msg/Trajectory",
      "usage": ["internal"],
      "topics": [],
      "description": "Individual trajectory representation used within Multi-Agent PID planning",
      "interface_text": "std_msgs/Header header\n\tbuiltin_interfaces/Time stamp\n\t\tint32 sec\n\t\tuint32 nanosec\n\tstring frame_id\ngeometry_msgs/PoseStamped[] poses\ngeometry_msgs/TwistStamped[] velocities\nfloat64[] times\nfloat64 total_time",
      "interface": [
        {
          "type": "object",
          "datatype": "std_msgs/Header",
          "label": "header",
          "typedef_text": "std_msgs/Header header"
        },
        {
          "type": "object_array",
          "datatype": "geometry_msgs/PoseStamped",
          "label": "poses",
          "typedef_text": "geometry_msgs/PoseStamped[] poses"
        },
        {
          "type": "object_array",
          "datatype": "geometry_msgs/TwistStamped",
          "label": "velocities",
          "typedef_text": "geometry_msgs/TwistStamped[] velocities"
        },
        {
          "type": "array",
          "datatype": "float64",
          "label": "times",
          "typedef_text": "float64[] times"
        },
        {
          "type": "primitive",
          "datatype": "float64",
          "label": "total_time",
          "typedef_text": "float64 total_time"
        }
      ]
    },
    {
      "datatype": "adore_ros2_msgs/msg/TrafficPrediction",
      "usage": ["internal"],
      "topics": [],
      "description": "Internal prediction data structure used during planning computations",
      "interface_text": "std_msgs/Header header\n\tbuiltin_interfaces/Time stamp\n\t\tint32 sec\n\t\tuint32 nanosec\n\tstring frame_id\nstring participant_id\nadore_ros2_msgs/VehiclePrediction[] predictions\nfloat64 prediction_horizon",
      "interface": [
        {
          "type": "object",
          "datatype": "std_msgs/Header",
          "label": "header",
          "typedef_text": "std_msgs/Header header"
        },
        {
          "type": "primitive",
          "datatype": "string",
          "label": "participant_id",
          "typedef_text": "string participant_id"
        },
        {
          "type": "object_array",
          "datatype": "adore_ros2_msgs/VehiclePrediction",
          "label": "predictions",
          "typedef_text": "adore_ros2_msgs/VehiclePrediction[] predictions"
        },
        {
          "type": "primitive",
          "datatype": "float64",
          "label": "prediction_horizon",
          "typedef_text": "float64 prediction_horizon"
        }
      ]
    },
    {
      "datatype": "adore_ros2_msgs/msg/VehiclePrediction",
      "usage": ["internal"],
      "topics": [],
      "description": "Individual vehicle prediction used within the multi-agent planning algorithm",
      "interface_text": "adore_ros2_msgs/Trajectory trajectory\nfloat64 probability\nstring prediction_type\ngeometry_msgs/Polygon[] occupied_space",
      "interface": [
        {
          "type": "object",
          "datatype": "adore_ros2_msgs/Trajectory",
          "label": "trajectory",
          "typedef_text": "adore_ros2_msgs/Trajectory trajectory"
        },
        {
          "type": "primitive",
          "datatype": "float64",
          "label": "probability",
          "typedef_text": "float64 probability"
        },
        {
          "type": "primitive",
          "datatype": "string",
          "label": "prediction_type",
          "typedef_text": "string prediction_type"
        },
        {
          "type": "object_array",
          "datatype": "geometry_msgs/Polygon",
          "label": "occupied_space",
          "typedef_text": "geometry_msgs/Polygon[] occupied_space"
        }
      ]
    }
  ]
}
```
