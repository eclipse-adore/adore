/********************************************************************************
 * Copyright (C) 2024-2025 German Aerospace Center (DLR).
 * Eclipse ADORe, Automated Driving Open Research https://eclipse.org/adore
 *
 * This program and the accompanying materials are made available under the
 * terms of the Eclipse Public License 2.0 which is available at
 * http://www.eclipse.org/legal/epl-2.0.
 *
 * SPDX-License-Identifier: EPL-2.0
 *
 * Contributors:
 *    Marko Mizdrak
 ********************************************************************************/
#include "adore_dynamics_conversions.hpp"

namespace adore
{
namespace dynamics
{
namespace conversions
{

void
update_state_with_odometry( VehicleStateDynamic& state, const nav_msgs::msg::Odometry& odom )
{
  state.x = odom.pose.pose.position.x;
  state.y = odom.pose.pose.position.y;
  state.z = odom.pose.pose.position.z;

  state.yaw_angle = adore::math::get_yaw( odom.pose.pose.orientation );
  state.vx        = odom.twist.twist.linear.x;
  state.vy        = odom.twist.twist.linear.y;
  state.yaw_rate  = odom.twist.twist.angular.z;

  state.time = static_cast<double>( odom.header.stamp.sec ) + 1e-9 * static_cast<double>( odom.header.stamp.nanosec );
}

adore_ros2_msgs::msg::VehicleCommand
to_ros_msg( const VehicleCommand& command )
{
  adore_ros2_msgs::msg::VehicleCommand msg;
  msg.steering_angle = command.steering_angle;
  msg.acceleration   = command.acceleration;
  return msg;
}

VehicleCommand
to_cpp_type( const adore_ros2_msgs::msg::VehicleCommand& msg )
{
  VehicleCommand command;
  command.steering_angle = msg.steering_angle;
  command.acceleration   = msg.acceleration;
  return command;
}

adore_ros2_msgs::msg::VehicleStateDynamic
to_ros_msg( const VehicleStateDynamic& state )
{
  adore_ros2_msgs::msg::VehicleStateDynamic msg;
  msg.time           = state.time;
  msg.x              = state.x;
  msg.y              = state.y;
  msg.z              = state.z;
  msg.vx             = state.vx;
  msg.vy             = state.vy;
  msg.yaw_angle      = state.yaw_angle;
  msg.yaw_rate       = state.yaw_rate;
  msg.ax             = state.ax;
  msg.ay             = state.ay;
  msg.steering_angle = state.steering_angle;
  msg.steering_rate  = state.steering_rate;
  return msg;
}

VehicleStateDynamic
to_cpp_type( const adore_ros2_msgs::msg::VehicleStateDynamic& msg )
{
  VehicleStateDynamic state;
  state.time           = msg.time;
  state.x              = msg.x;
  state.y              = msg.y;
  state.z              = msg.z;
  state.vx             = msg.vx;
  state.vy             = msg.vy;
  state.yaw_angle      = msg.yaw_angle;
  state.yaw_rate       = msg.yaw_rate;
  state.ax             = msg.ax;
  state.ay             = msg.ay;
  state.steering_angle = msg.steering_angle;
  state.steering_rate  = msg.steering_rate;
  return state;
}

adore_ros2_msgs::msg::GearState
to_ros_msg( const GearState& gear )
{
  adore_ros2_msgs::msg::GearState msg;
  msg.gear_state = static_cast<uint8_t>( gear );
  return msg;
}

GearState
to_cpp_type( const adore_ros2_msgs::msg::GearState& msg )
{
  return static_cast<GearState>( msg.gear_state );
}

adore_ros2_msgs::msg::VehicleInfo
to_ros_msg( const VehicleInfo& info )
{
  adore_ros2_msgs::msg::VehicleInfo msg;
  msg.gear_state                    = to_ros_msg( info.gear_state );
  msg.wheel_speed                   = info.wheel_speed;
  msg.left_indicator_on             = info.left_indicator_on;
  msg.right_indicator_on            = info.right_indicator_on;
  msg.automatic_steering_on         = info.automatic_steering_on;
  msg.automatic_acceleration_on     = info.automatic_acceleration_on;
  msg.automatic_acceleration_active = info.automatic_acceleration_active;
  msg.clearance                     = info.clearance;
  return msg;
}

VehicleInfo
to_cpp_type( const adore_ros2_msgs::msg::VehicleInfo& msg )
{
  VehicleInfo info;
  info.gear_state                    = to_cpp_type( msg.gear_state );
  info.wheel_speed                   = msg.wheel_speed;
  info.left_indicator_on             = msg.left_indicator_on;
  info.right_indicator_on            = msg.right_indicator_on;
  info.automatic_steering_on         = msg.automatic_steering_on;
  info.automatic_acceleration_on     = msg.automatic_acceleration_on;
  info.automatic_acceleration_active = msg.automatic_acceleration_active;
  info.clearance                     = msg.clearance;
  return info;
}

// Existing functions converting VehicleStateDynamic to other ROS messages
nav_msgs::msg::Odometry
dynamic_state_to_odometry_msg( const VehicleStateDynamic& vehicle_state, rclcpp::Clock::SharedPtr clock )
{
  nav_msgs::msg::Odometry odometry_msg;

  // Set header timestamp using the provided clock
  odometry_msg.header.stamp = clock->now();

  // Set position
  odometry_msg.pose.pose.position.x = vehicle_state.x;
  odometry_msg.pose.pose.position.y = vehicle_state.y;
  odometry_msg.pose.pose.position.z = vehicle_state.z; // Assuming 3D

  // Set orientation based on yaw_angle (yaw angle)
  tf2::Quaternion car_orientation_quaternion;
  car_orientation_quaternion.setRPY( 0, 0, vehicle_state.yaw_angle );

  odometry_msg.pose.pose.orientation.x = car_orientation_quaternion.x();
  odometry_msg.pose.pose.orientation.y = car_orientation_quaternion.y();
  odometry_msg.pose.pose.orientation.z = car_orientation_quaternion.z();
  odometry_msg.pose.pose.orientation.w = car_orientation_quaternion.w();

  // Set linear velocity
  odometry_msg.twist.twist.linear.x = vehicle_state.vx;
  odometry_msg.twist.twist.linear.y = vehicle_state.vy;
  odometry_msg.twist.twist.linear.z = vehicle_state.ay; // Assuming 'ay' as z velocity

  // Set angular velocity (yaw rate)
  odometry_msg.twist.twist.angular.x = 0;
  odometry_msg.twist.twist.angular.y = 0;
  odometry_msg.twist.twist.angular.z = vehicle_state.yaw_rate;

  return odometry_msg;
}

geometry_msgs::msg::TransformStamped
vehicle_state_to_transform( const VehicleStateDynamic& vehicle_state, const rclcpp::Time& timestamp, const std::string& source_frame_id )
{
  geometry_msgs::msg::TransformStamped vehicle_frame;

  vehicle_frame.header.stamp    = timestamp;
  vehicle_frame.header.frame_id = "world";
  vehicle_frame.child_frame_id  = source_frame_id;

  vehicle_frame.transform.translation.x = vehicle_state.x;
  vehicle_frame.transform.translation.y = vehicle_state.y;
  vehicle_frame.transform.translation.z = vehicle_state.z; // Assuming 3D

  tf2::Quaternion q;
  q.setRPY( 0, 0, vehicle_state.yaw_angle );

  vehicle_frame.transform.rotation.x = q.x();
  vehicle_frame.transform.rotation.y = q.y();
  vehicle_frame.transform.rotation.z = q.z();
  vehicle_frame.transform.rotation.w = q.w();

  return vehicle_frame;
}

adore_ros2_msgs::msg::Trajectory
to_ros_msg( const Trajectory& trajectory )
{
  adore_ros2_msgs::msg::Trajectory msg;
  for( const auto& state : trajectory.states )
  {
    msg.states.push_back( to_ros_msg( state ) );
  }
  msg.label = trajectory.label;
  return msg;
}

Trajectory
to_cpp_type( const adore_ros2_msgs::msg::Trajectory& msg )
{
  Trajectory trajectory;
  for( const auto& ros_state : msg.states )
  {
    trajectory.states.push_back( to_cpp_type( ros_state ) );
  }
  trajectory.label = msg.label;
  return trajectory;
}

adore_ros2_msgs::msg::TrajectoryTranspose
transpose( const adore_ros2_msgs::msg::Trajectory& msg )
{
  adore_ros2_msgs::msg::TrajectoryTranspose transpose;

  for( const auto& ros_state : msg.states )
  {
    transpose.x.push_back( ros_state.x );
    transpose.y.push_back( ros_state.y );
    transpose.z.push_back( ros_state.z );
    transpose.vx.push_back( ros_state.vx );
    transpose.vy.push_back( ros_state.vy );
    transpose.ax.push_back( ros_state.ax );
    transpose.ay.push_back( ros_state.ay );
    transpose.yaw_angle.push_back( ros_state.yaw_angle );
    transpose.yaw_rate.push_back( ros_state.yaw_rate );
    transpose.steering_angle.push_back( ros_state.steering_angle );
    transpose.steering_rate.push_back( ros_state.steering_rate );
    transpose.time.push_back( ros_state.time );
  }
  return transpose;
}

adore_ros2_msgs::msg::TrafficParticipant
to_ros_msg( const TrafficParticipant& participant )
{
  adore_ros2_msgs::msg::TrafficParticipant msg;

  // Convert state
  msg.motion_state = to_ros_msg( participant.state );

  // Convert bounding box
  msg.physical_parameters = to_ros_msg( participant.physical_parameters );

  // Convert classification
  msg.classification.type_id = static_cast<uint8_t>( participant.classification );

  if ( participant.v2x_id.has_value() )
  {
    msg.v2x_station_id = static_cast<uint64_t>( participant.v2x_id.value() );
  }

  // Convert id
  msg.tracking_id = participant.id;

  // Optional goal point
  if( participant.goal_point )
  {
    msg.goal_point.x = participant.goal_point->x;
    msg.goal_point.y = participant.goal_point->y;
  }

  // Optional trajectory
  if( participant.trajectory )
  {
    msg.predicted_trajectory = to_ros_msg( *participant.trajectory );
  }

  // Optional route
  if( participant.route )
  {
    msg.route = map::conversions::to_ros_msg( *participant.route );
  }

  return msg;
}

TrafficParticipant
to_cpp_type( const adore_ros2_msgs::msg::TrafficParticipant& msg )
{
  // Convert state
  VehicleStateDynamic state = to_cpp_type( msg.motion_state );

  PhysicalVehicleParameters physical_parameters = to_cpp_type( msg.physical_parameters );

  // Convert classification
  TrafficParticipantClassification classification = static_cast<TrafficParticipantClassification>( msg.classification.type_id );

  // Construct the participant
  TrafficParticipant participant( state, msg.tracking_id, classification, physical_parameters );

  if ( msg.v2x_station_id != 0 )
  {
    participant.v2x_id =  static_cast<uint64_t>( msg.v2x_station_id ); 
  }

  // Optional goal point
  if( msg.goal_point.x != 0.0 || msg.goal_point.y != 0.0 )
  {
    adore::math::Point2d goal_point;
    goal_point.x           = msg.goal_point.x;
    goal_point.y           = msg.goal_point.y;
    participant.goal_point = goal_point;
  }

  // Optional trajectory
  if( !msg.predicted_trajectory.states.empty() )
  {
    participant.trajectory = to_cpp_type( msg.predicted_trajectory );
  }

  // Optional route
  if( !msg.route.center_points.empty() )
  {
    participant.route = adore::map::conversions::to_cpp_type( msg.route );
  }

  return participant;
}

adore_ros2_msgs::msg::TrafficParticipantSet
to_ros_msg( const TrafficParticipantSet& participant_set )
{
  adore_ros2_msgs::msg::TrafficParticipantSet msg;

  for( const auto& [id, participant] : participant_set.participants )
  {
    adore_ros2_msgs::msg::TrafficParticipantDetection detection_msg;

    // Convert participant
    detection_msg.participant_data = to_ros_msg( participant );

    // Populate detection information (default example)
    detection_msg.detection_by_sensor = adore_ros2_msgs::msg::TrafficParticipantDetection::UNDEFINED;

    msg.data.push_back( detection_msg );
  }
  if( participant_set.validity_area )
  {
    msg.validity_area = math::conversions::to_ros_msg( participant_set.validity_area.value() );
  }

  return msg;
}

TrafficParticipantSet
to_cpp_type( const adore_ros2_msgs::msg::TrafficParticipantSet& msg )
{
  TrafficParticipantSet participant_set;

  for( const auto& detection : msg.data )
  {
    const auto&        participant_msg = detection.participant_data;
    TrafficParticipant participant     = to_cpp_type( participant_msg );

    participant_set.participants[participant.id] = participant;
  }
  if( msg.validity_area.points.size() > 5 )
  {
    participant_set.validity_area = math::conversions::to_cpp_type( msg.validity_area );
  }

  return participant_set;
}

adore_ros2_msgs::msg::PhysicalVehicleParameters
to_ros_msg( const PhysicalVehicleParameters& cpp )
{
  adore_ros2_msgs::msg::PhysicalVehicleParameters msg;

  msg.cog_to_front_axle           = cpp.cog_to_front_axle;
  msg.rear_axle_to_cog            = cpp.rear_axle_to_cog;
  msg.wheelbase                   = cpp.wheelbase;
  msg.front_axle_to_front_border  = cpp.front_axle_to_front_border;
  msg.rear_border_to_rear_axle    = cpp.rear_border_to_rear_axle;
  msg.mass                        = cpp.mass;
  msg.friction_coefficient        = cpp.friction_coefficient;
  msg.cog_height                  = cpp.cog_height;
  msg.front_tire_stiffness        = cpp.front_tire_stiffness;
  msg.rear_tire_stiffness         = cpp.rear_tire_stiffness;
  msg.rotational_inertia_div_mass = cpp.rotational_inertia_div_mass;
  msg.front_track_width           = cpp.front_track_width;
  msg.rear_track_width            = cpp.rear_track_width;
  msg.steering_ratio              = cpp.steering_ratio;
  msg.steering_angle_max          = cpp.steering_angle_max;
  msg.steering_angle_min          = cpp.steering_angle_min;
  msg.cornering_stiffness         = cpp.cornering_stiffness;
  msg.brake_balance_front         = cpp.brake_balance_front;
  msg.acceleration_balance_front  = cpp.acceleration_balance_front;
  msg.body_width                  = cpp.body_width;
  msg.body_length                 = cpp.body_length;
  msg.body_height                 = cpp.body_height;

  return msg;
}

PhysicalVehicleParameters
to_cpp_type( const adore_ros2_msgs::msg::PhysicalVehicleParameters& msg )
{
  PhysicalVehicleParameters cpp;

  cpp.cog_to_front_axle           = msg.cog_to_front_axle;
  cpp.rear_axle_to_cog            = msg.rear_axle_to_cog;
  cpp.wheelbase                   = msg.wheelbase;
  cpp.front_axle_to_front_border  = msg.front_axle_to_front_border;
  cpp.rear_border_to_rear_axle    = msg.rear_border_to_rear_axle;
  cpp.mass                        = msg.mass;
  cpp.friction_coefficient        = msg.friction_coefficient;
  cpp.cog_height                  = msg.cog_height;
  cpp.front_tire_stiffness        = msg.front_tire_stiffness;
  cpp.rear_tire_stiffness         = msg.rear_tire_stiffness;
  cpp.rotational_inertia_div_mass = msg.rotational_inertia_div_mass;
  cpp.front_track_width           = msg.front_track_width;
  cpp.rear_track_width            = msg.rear_track_width;
  cpp.steering_ratio              = msg.steering_ratio;
  cpp.steering_angle_max          = msg.steering_angle_max;
  cpp.steering_angle_min          = msg.steering_angle_min;
  cpp.cornering_stiffness         = msg.cornering_stiffness;
  cpp.brake_balance_front         = msg.brake_balance_front;
  cpp.acceleration_balance_front  = msg.acceleration_balance_front;
  cpp.body_width                  = msg.body_width;
  cpp.body_length                 = msg.body_length;
  cpp.body_height                 = msg.body_height;

  return cpp;
}
} // namespace conversions
} // namespace dynamics
} // namespace adore
