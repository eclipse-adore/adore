/********************************************************************************
 * Copyright (c) 2025 Contributors to the Eclipse Foundation
 *
 * See the NOTICE file(s) distributed with this work for additional
 * information regarding copyright ownership.
 *
 * This program and the accompanying materials are made available under the
 * terms of the Eclipse Public License 2.0 which is available at
 * https://www.eclipse.org/legal/epl-2.0
 *
 * SPDX-License-Identifier: EPL-2.0
 ********************************************************************************/

#include "adore_node_status.hpp"

namespace adore
{
namespace status
{
  NodeStatus::NodeStatus()
  {

  }
 
  NodeStatus::NodeStatus(const adore_ros2_msgs::msg::NodeStatus& msg)
  {
   this->from_ros_msg(msg);
  }
 
   void NodeStatus::from_ros_msg(const adore_ros2_msgs::msg::NodeStatus& msg)
   {
    values.clear();
    overview.clear();

    time = msg.time;
    values = json::parse( msg.content_json );
    overview = msg.overview;
   }
   
   adore_ros2_msgs::msg::NodeStatus NodeStatus::as_ros_msg(const double& current_time)
   {
    adore_ros2_msgs::msg::NodeStatus response_msg;

    response_msg.time = current_time;
    response_msg.content_json = values.dump();
    response_msg.overview = overview;

    return response_msg;
   }

   void NodeStatus::clear()
   {
    values.clear();
    overview.clear();
   }

} // namespace logging
} // namespace adore
