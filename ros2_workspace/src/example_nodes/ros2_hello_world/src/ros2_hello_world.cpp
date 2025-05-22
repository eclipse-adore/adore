/********************************************************************************
 * Copyright (C) 2017-2020 German Aerospace Center (DLR).
 * Eclipse ADORe, Automated Driving Open Research https://eclipse.org/adore
 *
 * This program and the accompanying materials are made available under the
 * terms of the Eclipse Public License 2.0 which is available at
 * http://www.eclipse.org/legal/epl-2.0.
 *
 * SPDX-License-Identifier: EPL-2.0
 *
 * Contributors:
 *    <Author-name>
 ********************************************************************************/

#include <chrono>
#include <functional>
#include <memory>
#include <string>
#include "rclcpp/rclcpp.hpp"
#include "std_msgs/msg/string.hpp"

using namespace std::chrono_literals;

class Ros2HelloWorld : public rclcpp::Node
{
  private:
    /******************************* PUBLISHERS RELATED MEMBERS ************************************************************/
    rclcpp::TimerBase::SharedPtr mainTimer;

    rclcpp::Publisher<std_msgs::msg::String>::SharedPtr publisherString;

    /******************************* SUBSCRIBERS RELATED MEMBERS ************************************************************/
    rclcpp::Subscription<std_msgs::msg::String>::SharedPtr subscriberString;

    /******************************* OTHER MEMBERS *************************************************************************/
    std_msgs::msg::String latestRecievedStringMessage;

  public:
    Ros2HelloWorld() : Node("ros2_hello_world")
    {
      mainTimer = this->create_wall_timer(100ms, std::bind(&Ros2HelloWorld::Run, this));
      publisherString = this->create_publisher<std_msgs::msg::String>("publishing_topic_name", 10);

      subscriberString = this->create_subscription<std_msgs::msg::String>("subscribing_topic_name", 10, std::bind(&Ros2HelloWorld::SubscriberStringCallback, this, std::placeholders::_1));
    }

    /******************************* PUBLISHER RELATED FUNCTIONS ************************************************************/

    void Run(){
      std_msgs::msg::String message;
      message.data = "Hello, World!";
      RCLCPP_INFO(this->get_logger(), "Publishing: '%s'", message.data.c_str());
      publisherString->publish(message);
      rclcpp::sleep_for(std::chrono::seconds(1));
    }

    /******************************* SUBSCRIBER RELATED FUNCTIONS************************************************************/

    void SubscriberStringCallback(std_msgs::msg::String msg){
      latestRecievedStringMessage = msg;
    }
};

int main(int argc, char * argv[]){
  rclcpp::init(argc, argv);
  rclcpp::spin(std::make_shared<Ros2HelloWorld>());
  rclcpp::shutdown();
  return 0;
}
