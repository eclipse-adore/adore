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
#include "adore_math_conversions.hpp"

#include <adore_ros2_msgs/msg/polygon2d.hpp>

#include <geometry_msgs/msg/point.hpp>

namespace adore
{
namespace math
{
namespace conversions
{
Point2d
to_cpp_type( const adore_ros2_msgs::msg::Point2d& msg )
{
  Point2d point;
  point.x = msg.x;
  point.y = msg.y;
  return point;
}

adore_ros2_msgs::msg::Point2d
to_ros_msg( const Point2d& point )
{
  adore_ros2_msgs::msg::Point2d msg;
  msg.x = point.x;
  msg.y = point.y;

  return msg;
}

Polygon2d
to_cpp_type( const adore_ros2_msgs::msg::Polygon2d& msg )
{
  Polygon2d polygon;
  polygon.points.reserve( msg.points.size() );

  for( const auto& ros_point : msg.points )
  {
    polygon.points.push_back( to_cpp_type( ros_point ) );
  }
  return polygon;
}

adore_ros2_msgs::msg::Polygon2d
to_ros_msg( const Polygon2d& polygon )
{
  adore_ros2_msgs::msg::Polygon2d msg;
  msg.points.reserve( polygon.points.size() );

  for( const auto& p : polygon.points )
  {
    msg.points.push_back( to_ros_msg( p ) );
  }
  return msg;
}

} // namespace conversions
} // namespace math
} // namespace adore
