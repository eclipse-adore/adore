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

#include "adore_math/polygon.h"
#include "adore_ros2_msgs/msg/point2d.hpp"
#include "adore_ros2_msgs/msg/polygon2d.hpp"

namespace adore
{
namespace math

{
namespace conversions
{
Point2d to_cpp_type( const adore_ros2_msgs::msg::Point2d& msg );

adore_ros2_msgs::msg::Point2d to_ros_msg( const Point2d& msg );

Polygon2d to_cpp_type( const adore_ros2_msgs::msg::Polygon2d& msg );

adore_ros2_msgs::msg::Polygon2d to_ros_msg( const Polygon2d& msg );


} // namespace conversions
} // namespace math
} // namespace adore