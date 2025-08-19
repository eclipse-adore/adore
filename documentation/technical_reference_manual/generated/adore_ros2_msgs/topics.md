## Topics
The follow section enumerates the ROS Topics and Datatypes used by ADORe.


| Topic | Datatype | Description |
|-------|----------|-------------|
| `/ego_vehicle/infrastructure_info` | `adore_ros2_msgs/msg/InfrastructureInfo` | Infrastructure element data including position, orientation, and validity area for roadside infrastructure |
| `/ego_vehicle/vehicle_state/dynamic` | `adore_ros2_msgs/msg/VehicleStateDynamic` | Real-time vehicle dynamics including position, velocity, acceleration, yaw angle, and steering information |
| `/parameter_events` | `rcl_interfaces/msg/ParameterEvent` | ROS2 parameter change notifications for dynamic reconfiguration |
| `/tf` | `tf2_msgs/msg/TFMessage` | Dynamic coordinate frame transforms for spatial relationships between vehicle components |
| `/tf_static` | `tf2_msgs/msg/TFMessage` | Static coordinate frame transforms that don't change over time |
| `/ego_vehicle/map_grid` | `nav_msgs/msg/OccupancyGrid` | 2D occupancy grid representation of the environment for visualization |
| `/ego_vehicle/visualize_ego_vehicle` | `visualization_msgs/msg/MarkerArray` | 3D visualization markers representing the ego vehicle for RViz display |
| `/rosout` | `rcl_interfaces/msg/Log` | ROS2 logging output with different severity levels (DEBUG, INFO, WARN, ERROR, FATAL) |

