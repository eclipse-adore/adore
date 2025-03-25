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
#include "adore_map/map.hpp"
#include "adore_map/route.hpp"
#include "adore_ros2_msgs/msg/map.hpp"
#include "adore_ros2_msgs/msg/map_connection.hpp"
#include "adore_ros2_msgs/msg/map_lane.hpp"
#include "adore_ros2_msgs/msg/map_point.hpp"
#include "adore_ros2_msgs/msg/map_road.hpp"
#include "adore_ros2_msgs/msg/route.hpp"

namespace adore
{
namespace map

{
namespace conversions
{


// Convert MapPoint to ROS message
adore_ros2_msgs::msg::MapPoint to_ros_msg( const MapPoint& cpp_point );

// Convert ROS MapPoint message to C++ MapPoint
MapPoint to_cpp_type( const adore_ros2_msgs::msg::MapPoint& ros_point );

// Convert Lane to ROS message
adore_ros2_msgs::msg::MapLane to_ros_msg( const Lane& cpp_lane );

// Convert ROS Lane message to C++ Lane
Lane to_cpp_type( const adore_ros2_msgs::msg::MapLane& ros_lane );

// Convert Connection to ROS message
adore_ros2_msgs::msg::MapConnection to_ros_msg( const Connection& cpp_connection );
// Convert ROS Connection message to C++ Connection
Connection to_cpp_type( const adore_ros2_msgs::msg::MapConnection& ros_connection );
// Convert Road to ROS message
adore_ros2_msgs::msg::MapRoad to_ros_msg( const Road& cpp_road );

// Convert ROS Road message to C++ Road
Road to_cpp_type( const adore_ros2_msgs::msg::MapRoad& ros_road );

// Convert Map to ROS message
adore_ros2_msgs::msg::Map to_ros_msg( const Map& cpp_map );

// Convert ROS Map message to C++ Map
Map to_cpp_type( const adore_ros2_msgs::msg::Map& ros_map );

// Convert Map to ROS message
adore_ros2_msgs::msg::Map to_ros_msg( const Map& cpp_map );

// Convert from Route message to Route C++ type
RouteSection to_cpp_type( const adore_ros2_msgs::msg::RouteSection& msg );

// Convert from RouteSection (C++ struct) to RouteSection.msg
adore_ros2_msgs::msg::RouteSection to_ros_msg( const RouteSection& section );

// Convert from Route message to Route C++ type
Route to_cpp_type( const adore_ros2_msgs::msg::Route& msg );

// Convert from Route (C++ struct) to Route.msg
adore_ros2_msgs::msg::Route to_ros_msg( const Route& route );

} // namespace conversions
} // namespace map
} // namespace adore