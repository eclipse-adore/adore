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
        auto start_time = std::chrono::high_resolution_clock::now();
        
        std::lock_guard<std::mutex> lock(data_mutex_);
        
        RCLCPP_INFO(this->get_logger(), "Traffic participants received: %zu", msg.data.size());
        
        if (msg.data.empty()) {
            RCLCPP_WARN_THROTTLE(this->get_logger(), *this->get_clock(), 2000,
                                 "No traffic participants detected in scene");
            RCLCPP_ERROR(this->get_logger(), "Traffic participants empty: YES");
        }
        
        for (size_t i = 0; i < msg.data.size(); ++i) {
            RCLCPP_INFO(this->get_logger(), "Debug information participant index: %d", static_cast<int>(i));
        }
        
        latest_traffic_data_ = dynamics::conversions::to_cpp_type( msg );

        if ( ego_traffic_data_received_ )
        {
            latest_traffic_data_.update_traffic_participants(latest_ego_traffic_data_);
            RCLCPP_INFO(this->get_logger(), "Ego traffic data merged successfully");
        }
        else
        {
            RCLCPP_ERROR(this->get_logger(), "Ego traffic data not available: NO");
            RCLCPP_WARN_THROTTLE(this->get_logger(), *this->get_clock(), 3000,
                                 "Ego traffic data has not been received yet");
        }

        traffic_data_received_ = true;
        
        auto end_time = std::chrono::high_resolution_clock::now();
        auto diff = std::chrono::duration_cast<std::chrono::milliseconds>(end_time - start_time);
        RCLCPP_INFO(this->get_logger(), "Time taken traffic callback: %ld milliseconds", diff.count());
        
        if (diff.count() > 50) {
            RCLCPP_WARN_THROTTLE(this->get_logger(), *this->get_clock(), 5000,
                                 "Traffic callback taking excessive time: %ld ms", diff.count());
        }
    }
    
    void trafficEgoCallback(const adore_ros2_msgs::msg::TrafficParticipant& msg)
    {
        auto start_time = std::chrono::high_resolution_clock::now();
        
        std::lock_guard<std::mutex> lock(data_mutex_);
        
        RCLCPP_INFO(this->get_logger(), "Ego traffic participant received");
        
        latest_ego_traffic_data_ = dynamics::conversions::to_cpp_type( msg );
        ego_traffic_data_received_ = true;
        
        auto end_time = std::chrono::high_resolution_clock::now();
        auto diff = std::chrono::duration_cast<std::chrono::milliseconds>(end_time - start_time);
        RCLCPP_INFO(this->get_logger(), "Time taken ego callback: %ld milliseconds", diff.count());
    }

    void mapCallback(const adore_ros2_msgs::msg::Map& msg)
    {
        auto start_time = std::chrono::high_resolution_clock::now();
        
        std::lock_guard<std::mutex> lock(data_mutex_);
        
        RCLCPP_INFO(this->get_logger(), "Map data received");
        
        latest_map_data_ = map::conversions::to_cpp_type( msg );
        map_data_received_ = true;
        
        auto end_time = std::chrono::high_resolution_clock::now();
        auto diff = std::chrono::duration_cast<std::chrono::milliseconds>(end_time - start_time);
        RCLCPP_INFO(this->get_logger(), "Time taken map callback: %ld milliseconds", diff.count());
    }

    void planningCallback()
    {
        auto planning_start_time = std::chrono::high_resolution_clock::now();
        
        std::lock_guard<std::mutex> lock(data_mutex_);
        
        if (!traffic_data_received_ || !map_data_received_) {
            RCLCPP_DEBUG_THROTTLE(this->get_logger(), *this->get_clock(), 1000,
                                  "Waiting for data - Traffic: %s, Map: %s",
                                  traffic_data_received_ ? "OK" : "Missing",
                                  map_data_received_ ? "OK" : "Missing");
                                  
            RCLCPP_WARN_THROTTLE(this->get_logger(), *this->get_clock(), 5000,
                                 "Planning blocked waiting for required data inputs");
                                  
            if (!traffic_data_received_) {
                RCLCPP_ERROR(this->get_logger(), "Traffic data not ready: NO");
            }
            if (!map_data_received_) {
                RCLCPP_ERROR(this->get_logger(), "Map data not ready: NO");
            }
            return;
        }

        if (!traffic_data_received_ || !map_data_received_) {
            RCLCPP_ERROR(this->get_logger(), "Data validation failed: YES");
            return;
        }

        auto planner_start_time = std::chrono::high_resolution_clock::now();
        
        auto status_from_planner = multi_agent_PID_planner.plan_trajectories( latest_traffic_data_ );
        
        auto planner_end_time = std::chrono::high_resolution_clock::now();
        auto planner_diff = std::chrono::duration_cast<std::chrono::milliseconds>(planner_end_time - planner_start_time);
        RCLCPP_INFO(this->get_logger(), "Time taken planner execution: %ld milliseconds", planner_diff.count());

        if (status_from_planner.overview_state != 0) {
            RCLCPP_ERROR(this->get_logger(), "Planner execution failed: YES");
            RCLCPP_ERROR(this->get_logger(), "Planner status code: %d", status_from_planner.overview_state);
            RCLCPP_WARN_THROTTLE(this->get_logger(), *this->get_clock(), 3000,
                                 "Repeated planner failures detected with status: %d", status_from_planner.overview_state);
        } else {
            RCLCPP_INFO(this->get_logger(), "Planner execution successful: %d", status_from_planner.overview_state);
        }

        if (planner_diff.count() > 80) {
            RCLCPP_WARN_THROTTLE(this->get_logger(), *this->get_clock(), 2000,
                                 "Planner execution time exceeding target: %ld ms", planner_diff.count());
        }

        prediction_publisher_->publish( dynamics::conversions::to_ros_msg( latest_traffic_data_  ));

        auto planning_end_time = std::chrono::high_resolution_clock::now();
        auto planning_diff = std::chrono::duration_cast<std::chrono::milliseconds>(planning_end_time - planning_start_time);
        RCLCPP_INFO(this->get_logger(), "Time taken complete planning cycle: %ld milliseconds", planning_diff.count());
        
        if (planning_diff.count() > 95) {
            RCLCPP_WARN_THROTTLE(this->get_logger(), *this->get_clock(), 1000,
                                 "Planning cycle approaching deadline: %ld ms (target: 100ms)", planning_diff.count());
        }
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
        RCLCPP_ERROR(node->get_logger(), "Exception occurred: YES");
        return 1;
    }
    
    RCLCPP_INFO(node->get_logger(), "Traffic Predictor Node shutting down");
    rclcpp::shutdown();
    return 0;
}
