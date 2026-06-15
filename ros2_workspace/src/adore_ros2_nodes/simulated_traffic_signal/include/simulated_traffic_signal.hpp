#include <string>
#include <vector>

#include "adore_ros2_msgs/msg/traffic_signals.hpp"

#include "std_msgs/msg/header.hpp"
#include "std_msgs/msg/string.hpp"
#include <rclcpp/rclcpp.hpp>

using namespace std::chrono_literals;

namespace adore
{
namespace simulated_traffic_signal
{
using TrafficSignalsMsg = adore_ros2_msgs::msg::TrafficSignals;
using TrafficSignalMsg  = adore_ros2_msgs::msg::TrafficSignal;

class SimulatedTrafficSignal : public rclcpp::Node
{
public:

  explicit SimulatedTrafficSignal( const rclcpp::NodeOptions& options );

private:

  struct TrafficLightConfig
  {
    double       x;
    double       y;
    double       red_duration;
    double       yellow_duration;
    double       green_duration;
    int32_t      state;
    rclcpp::Time last_transition_time;
  };

  bool permanent_red = false;

  void update_signals();
  void user_input_callback( const std_msgs::msg::String& msg );

  rclcpp::Publisher<TrafficSignalsMsg>::SharedPtr        publisher;
  rclcpp::Subscription<std_msgs::msg::String>::SharedPtr subscriber_user_input;
  rclcpp::TimerBase::SharedPtr                           timer;

  std::vector<TrafficLightConfig> traffic_lights;
};
} // namespace simulated_traffic_signal
} // namespace adore