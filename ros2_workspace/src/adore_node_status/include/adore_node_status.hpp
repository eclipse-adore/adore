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

#pragma once

#include <iostream>
#include <string>
#include <unordered_map>
#include <vector>
#include <optional>

#include <nlohmann/json.hpp>
#include <nlohmann/json_fwd.hpp>

using json = nlohmann::json;

#include "adore_ros2_msgs/msg/node_status.hpp"

namespace adore
{
namespace status
{
 class NodeStatus
 {
  public:

   NodeStatus();
   NodeStatus(const adore_ros2_msgs::msg::NodeStatus& msg);

   adore_ros2_msgs::msg::NodeStatus as_ros_msg(const double& current_time);
   void from_ros_msg(const adore_ros2_msgs::msg::NodeStatus& msg);
  
   template<typename T>
   void add_info(const std::string& key, const T& value)
   {
    json jvalue = json( value );
    values[key] = jvalue;
   }

   template<typename T>
   std::optional<T> get_info(const std::string& key)
   {
    if ( !values.contains(key) )
     return {};

    auto it = values.find(key);

    if( it == values.end() )
     return {};

    try
    {
     return it.value().get<T>(); 
    }
    catch( ... )
    {
     return {};
    }
   }

   void clear();

   double time;
   std::string overview;

  private:

   json values = json::object();
 };
} // namespace logging
} // namespace adore
