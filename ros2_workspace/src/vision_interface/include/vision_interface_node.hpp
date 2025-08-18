#include <string>
#include <vector>

#include "adore_ros2_msgs/msg/traffic_signals.hpp"

#include "std_msgs/msg/header.hpp"
#include "std_msgs/msg/string.hpp"
#include "vision_msgs/msg/detection2_d_array.hpp"
#include <rclcpp/rclcpp.hpp>

namespace adore
{

using TrafficSignalsMsg = adore_ros2_msgs::msg::TrafficSignals;
using TrafficSignalMsg  = adore_ros2_msgs::msg::TrafficSignal;

class VisionInterface : public rclcpp::Node
{
public:

  VisionInterface();

private:

  void                                            detection_2d_callback( const vision_msgs::msg::Detection2DArray& msg );
  rclcpp::Publisher<TrafficSignalsMsg>::SharedPtr publisher_traffic_signals;
  rclcpp::Subscription<vision_msgs::msg::Detection2DArray>::SharedPtr detection_subscriber;

  std::string traffic_signals_publishing_topic = "traffic_signals";
  std::string detection_subscribing_topic      = "/perception/vision/detections";

  std::pair<double, double> world_xy_demo_signal = { 0.0, 0.0 }; // Example coordinates for demo purposes
};
} // namespace adore
