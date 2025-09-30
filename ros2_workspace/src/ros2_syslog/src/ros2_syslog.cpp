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

#include "rclcpp/rclcpp.hpp"
#include "std_msgs/msg/string.hpp"
#include <syslog.h>
#include <iostream>
#include <ctime>

const int MAX_MESSAGES_PER_SECOND = 10;


class RateLimiter {
public:
  RateLimiter(int maxMessagesPerSecond)
      : maxMessagesPerSecond_(maxMessagesPerSecond),
        lastUpdateTime_(std::time(0)),
        tokens_(maxMessagesPerSecond) {}

  bool canLog() {
    updateTokens();
    if (tokens_ > 0) {
      --tokens_;
      return true;
    } else {
      return false;
    }
  }

private:
  void updateTokens() {
    std::time_t now = std::time(0);
    double elapsedSeconds = difftime(now, lastUpdateTime_);
    lastUpdateTime_ = now;

    tokens_ += elapsedSeconds * maxMessagesPerSecond_;
    if (tokens_ > maxMessagesPerSecond_) {
      tokens_ = maxMessagesPerSecond_;
    }
  }

  int maxMessagesPerSecond_;
  std::time_t lastUpdateTime_;
  double tokens_;
};

class ROS2Syslog : public rclcpp::Node {
public:
  ROS2Syslog() : Node("ros2_syslog_node") {
    subscription_ = create_subscription<std_msgs::msg::String>(
        "telemetry",
        10, [this](const std_msgs::msg::String::SharedPtr msg) {
          if (rateLimiter_.canLog()) {
            RCLCPP_INFO(get_logger(), "Telemetry message received: '%s'", msg->data.c_str());
            syslog(LOG_INFO, "ros2: %s", msg->data.c_str());
          } else {
            std::cerr << "ERROR: Syslog rate limit exceeded. ROS2 Message not logged to syslog.\n";
          }
        });

    publisher_ = create_publisher<std_msgs::msg::String>("telemetry", 10);
    auto message = std_msgs::msg::String();
    message.data = "ROS2 Syslog Telemetry system started";
    publisher_->publish(message);
  }

private:
  rclcpp::Subscription<std_msgs::msg::String>::SharedPtr subscription_;
  rclcpp::Publisher<std_msgs::msg::String>::SharedPtr publisher_;
  RateLimiter rateLimiter_{MAX_MESSAGES_PER_SECOND};
};

int main(int argc, char *argv[]) {
  rclcpp::init(argc, argv);

  rclcpp::spin(std::make_shared<ROS2Syslog>());

  rclcpp::shutdown();
  return 0;
}

