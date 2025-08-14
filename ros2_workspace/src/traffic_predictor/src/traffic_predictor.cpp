/********************************************************************************
 * Copyright (C) 2017-2025 German Aerospace Center (DLR).
 * Eclipse ADORe, Automated Driving Open Research https://eclipse.org/adore
 *
 * This program and the accompanying materials are made available under the
 * terms of the Eclipse Public License 2.0 which is available at
 * http://www.eclipse.org/legal/epl-2.0.
 *
 * SPDX-License-Identifier: EPL-2.0
 *
 * Contributors:
 *    Giovanni Lucente
 ********************************************************************************/

#include <rclcpp/rclcpp.hpp>
#include <std_msgs/msg/header.hpp>
#include <geometry_msgs/msg/point.hpp>

#include "adore_ros2_msgs/msg/traffic_participant_set.hpp"
#include "adore_ros2_msgs/msg/traffic_participant.hpp"
#include "adore_ros2_msgs/msg/traffic_participant_detection.hpp"
#include "adore_ros2_msgs/msg/vehicle_state_dynamic.hpp"
#include "adore_ros2_msgs/msg/trajectory.hpp"
#include "adore_ros2_msgs/msg/traffic_prediction.hpp"
#include "adore_ros2_msgs/msg/vehicle_prediction.hpp"
#include "adore_ros2_msgs/msg/route.hpp"

#include "dynamics/traffic_participant.hpp"

#include <memory>
#include <vector>
#include <chrono>
#include "adore_map_conversions.hpp"
#include <adore_dynamics_conversions.hpp>
#include <adore_map/map.hpp>
#include "planning/multi_agent_PID.hpp"

namespace adore
{
namespace planning
{

class TrafficPredictorNode : public rclcpp::Node
{
public:

    planner::MultiAgentPID              multi_agent_PID_planner;

    TrafficPredictorNode() : Node("traffic_predictor_node")
    {
        RCLCPP_INFO(this->get_logger(), "Initializing Traffic Predictor Node");
        
       traffic_subscriber_ = this->create_subscription<adore_ros2_msgs::msg::TrafficParticipantSet>(
            "ego_vehicle/traffic_participants", 10,
            std::bind(&TrafficPredictorNode::trafficCallback, this, std::placeholders::_1));

       ego_traffic_subscriber_ = this->create_subscription<adore_ros2_msgs::msg::TrafficParticipant>(
            "ego_vehicle/traffic_participant", 10,
            std::bind(&TrafficPredictorNode::trafficEgoCallback, this, std::placeholders::_1));

        map_subscriber_ = this->create_subscription<adore_ros2_msgs::msg::Map>(
            "ego_vehicle/local_map", 10,
            std::bind(&TrafficPredictorNode::mapCallback, this, std::placeholders::_1));

        prediction_publisher_ = this->create_publisher<adore_ros2_msgs::msg::TrafficParticipantSet>(
            "ego_vehicle/traffic_prediction", 10);

        timer_ = this->create_wall_timer(
            std::chrono::milliseconds(100),
            std::bind(&TrafficPredictorNode::planningCallback, this));

        RCLCPP_INFO(this->get_logger(), "Traffic Predictor Node initialized successfully");
    }

private:
    void trafficCallback(const adore_ros2_msgs::msg::TrafficParticipantSet& msg)
    {
        // RCLCPP_DEBUG(this->get_logger(), "Received traffic participant set with %zu participants", 
        //              msg->data.size());
        
        std::lock_guard<std::mutex> lock(data_mutex_);
        latest_traffic_data_ = dynamics::conversions::to_cpp_type( msg );

        if ( ego_traffic_data_received_ )
        {
            latest_traffic_data_.update_traffic_participants(latest_ego_traffic_data_);
        }

        traffic_data_received_ = true;
    }
    void trafficEgoCallback(const adore_ros2_msgs::msg::TrafficParticipant& msg)
    {
        // RCLCPP_DEBUG(this->get_logger(), "Received traffic participant set with %zu participants", 
        //              msg->data.size());
        
        std::lock_guard<std::mutex> lock(data_mutex_);
        latest_ego_traffic_data_ = dynamics::conversions::to_cpp_type( msg );
        ego_traffic_data_received_ = true;
    }

    void mapCallback(const adore_ros2_msgs::msg::Map& msg)
    {
        // RCLCPP_DEBUG(this->get_logger(), "Received map data with %zu elements", msg.data.size());
        
        std::lock_guard<std::mutex> lock(data_mutex_);
        latest_map_data_ = map::conversions::to_cpp_type( msg );
        map_data_received_ = true;
    }

    void planningCallback()
    {
        std::lock_guard<std::mutex> lock(data_mutex_);
        
        if (!traffic_data_received_ || !map_data_received_) {
            RCLCPP_DEBUG_THROTTLE(this->get_logger(), *this->get_clock(), 1000,
                                  "Waiting for data - Traffic: %s, Map: %s",
                                  traffic_data_received_ ? "OK" : "Missing",
                                  map_data_received_ ? "OK" : "Missing");
            return;
        }

        if (!traffic_data_received_ || !map_data_received_) {
            // RCLCPP_WARN(this->get_logger(), "Data pointers are null");
            return;
        }

        auto start_time = std::chrono::high_resolution_clock::now();
        
        int status_from_planner = multi_agent_PID_planner.plan_trajectories( latest_traffic_data_ );

        prediction_publisher_->publish( dynamics::conversions::to_ros_msg( latest_traffic_data_  ));

    }

    rclcpp::Subscription<adore_ros2_msgs::msg::TrafficParticipantSet>::SharedPtr traffic_subscriber_;
    rclcpp::Subscription<adore_ros2_msgs::msg::TrafficParticipant>::SharedPtr ego_traffic_subscriber_;
    rclcpp::Subscription<adore_ros2_msgs::msg::Map>::SharedPtr map_subscriber_;
    rclcpp::Publisher<adore_ros2_msgs::msg::TrafficParticipantSet>::SharedPtr prediction_publisher_;
    rclcpp::TimerBase::SharedPtr timer_;
    
    std::mutex data_mutex_;
    adore::dynamics::TrafficParticipantSet latest_traffic_data_;
    adore::dynamics::TrafficParticipant latest_ego_traffic_data_;
    adore::map::Map latest_map_data_;
    bool ego_traffic_data_received_ = false;
    bool traffic_data_received_ = false;
    bool map_data_received_ = false;
};

} // namespace planning
} // namespace adore

int main(int argc, char** argv)
{
    rclcpp::init(argc, argv);
    
    auto node = std::make_shared<adore::planning::TrafficPredictorNode>();
    
    RCLCPP_INFO(node->get_logger(), "Traffic Predictor Node starting...");
    
    try {
        rclcpp::spin(node);
    } catch (const std::exception& e) {
        RCLCPP_FATAL(node->get_logger(), "Node crashed: %s", e.what());
        return 1;
    }
    
    RCLCPP_INFO(node->get_logger(), "Traffic Predictor Node shutting down");
    rclcpp::shutdown();
    return 0;
}
