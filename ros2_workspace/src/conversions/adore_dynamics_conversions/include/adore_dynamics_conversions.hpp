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

#pragma once

#include "adore_map_conversions.hpp"
#include "adore_math/angles.h"
#include "adore_ros2_msgs/msg/gear_state.hpp"
#include "adore_ros2_msgs/msg/traffic_participant_set.hpp"
#include "adore_ros2_msgs/msg/trajectory.hpp"
#include "adore_ros2_msgs/msg/trajectory_transpose.hpp"
#include "adore_ros2_msgs/msg/vehicle_command.hpp"
#include "adore_ros2_msgs/msg/vehicle_info.hpp"
#include "adore_ros2_msgs/msg/vehicle_state_dynamic.hpp"
#include "adore_ros2_msgs/msg/vehicle_state_extended.hpp"

#include "dynamics/traffic_participant.hpp"
#include "dynamics/trajectory.hpp"
#include "geometry_msgs/msg/transform_stamped.hpp"
#include "nav_msgs/msg/odometry.hpp"
#include "rclcpp/rclcpp.hpp"
#include "tf2/LinearMath/Quaternion.h"
#include "tf2/utils.h"

namespace adore
{
namespace dynamics
{
namespace conversions
{
// Populate known state variables from odom data
void update_state_with_odometry( dynamics::VehicleStateDynamic& state, const nav_msgs::msg::Odometry& odom );

// Conversion from C++ type VehicleCommand to ROS2 message VehicleCommand
adore_ros2_msgs::msg::VehicleCommand to_ros_msg( const VehicleCommand& command );

// Conversion from ROS2 message VehicleCommand to C++ type VehicleCommand
VehicleCommand to_cpp_type( const adore_ros2_msgs::msg::VehicleCommand& msg );

// Conversion from C++ type VehicleStateDynamic to ROS2 message VehicleStateDynamic
adore_ros2_msgs::msg::VehicleStateDynamic to_ros_msg( const dynamics::VehicleStateDynamic& state );

// Conversion from ROS2 message VehicleStateDynamic to C++ type VehicleStateDynamic
dynamics::VehicleStateDynamic to_cpp_type( const adore_ros2_msgs::msg::VehicleStateDynamic& msg );

// Conversion from C++ type GearState to ROS2 message GearState
adore_ros2_msgs::msg::GearState to_ros_msg( const dynamics::GearState& gear );

// Conversion from ROS2 message GearState to C++ type GearState
dynamics::GearState to_cpp_type( const adore_ros2_msgs::msg::GearState& msg );

// Conversion from C++ type VehicleInfo to ROS2 message VehicleInfo
adore_ros2_msgs::msg::VehicleInfo to_ros_msg( const VehicleInfo& info );

// Conversion from ROS2 message VehicleInfo to C++ type VehicleInfo
VehicleInfo to_cpp_type( const adore_ros2_msgs::msg::VehicleInfo& msg );

nav_msgs::msg::Odometry dynamic_state_to_odometry_msg( const dynamics::VehicleStateDynamic& vehicle_state, rclcpp::Clock::SharedPtr clock );

geometry_msgs::msg::TransformStamped vehicle_state_to_transform( const dynamics::VehicleStateDynamic& vehicle_state,
                                                                 const rclcpp::Time&                  timestamp );

adore_ros2_msgs::msg::Trajectory to_ros_msg( const Trajectory& trajectory );

Trajectory to_cpp_type( const adore_ros2_msgs::msg::Trajectory& msg );

adore_ros2_msgs::msg::TrajectoryTranspose transpose( const adore_ros2_msgs::msg::Trajectory& msg );

adore_ros2_msgs::msg::TrafficParticipant to_ros_msg( const TrafficParticipant& participant );

TrafficParticipant to_cpp_type( const adore_ros2_msgs::msg::TrafficParticipant& msg );

adore_ros2_msgs::msg::TrafficParticipantSet to_ros_msg( const TrafficParticipantSet& participant_set );

TrafficParticipantSet to_cpp_type( const adore_ros2_msgs::msg::TrafficParticipantSet& msg );
} // namespace conversions
} // namespace dynamics
} // namespace adore
