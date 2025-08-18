// vision_interface.cpp
#include "vision_interface_node.hpp" // header with the two fixes noted above

#include <string>
#include <utility>
#include <vector>

#include "adore_ros2_msgs/msg/traffic_signal.hpp"
#include "adore_ros2_msgs/msg/traffic_signals.hpp"

#include "rclcpp/rclcpp.hpp"
#include "std_msgs/msg/header.hpp"
#include "vision_msgs/msg/detection2_d_array.hpp"

namespace adore
{

VisionInterface::VisionInterface() :
  rclcpp::Node( "vision_traffic_signal_node" )
{
  // Declare parameters and store directly in member variables (no get_parameter).
  traffic_signals_publishing_topic = declare_parameter<std::string>( "traffic_signals_publishing_topic", traffic_signals_publishing_topic );

  detection_subscribing_topic = declare_parameter<std::string>( "detection_subscribing_topic", detection_subscribing_topic );

  // world_xy_demo_signal as a 2-element array param; convert to std::pair.
  const auto xy = declare_parameter<std::vector<double>>( "world_xy_demo_signal",
                                                          { world_xy_demo_signal.first, world_xy_demo_signal.second } );
  if( xy.size() >= 2 )
  {
    world_xy_demo_signal = { xy[0], xy[1] };
  }
  else
  {
    RCLCPP_WARN( get_logger(), "Parameter 'world_xy_demo_signal' must have 2 elements; using defaults (0,0)." );
  }

  // Publisher on the configured topic
  publisher_traffic_signals = create_publisher<TrafficSignalsMsg>( traffic_signals_publishing_topic, rclcpp::QoS( 10 ).reliable() );

  // Subscriber on the configured topic (we ignore message content)
  detection_subscriber = create_subscription<vision_msgs::msg::Detection2DArray>( detection_subscribing_topic, rclcpp::SensorDataQoS(),
                                                                                  std::bind( &VisionInterface::detection_2d_callback, this,
                                                                                             std::placeholders::_1 ) );

  RCLCPP_INFO( get_logger(), "VisionInterface: subscribing '%s' -> publishing '%s'", detection_subscribing_topic.c_str(),
               traffic_signals_publishing_topic.c_str() );
}

void
VisionInterface::detection_2d_callback( const vision_msgs::msg::Detection2DArray& /*msg*/ )
{
  // For demo purposes Always publish: 1 red signal at the preloaded world (x,y)
  TrafficSignalsMsg out;
  out.header.stamp    = now();
  out.header.frame_id = "world"; // fixed for the demo; add a member/param if you want this configurable

  TrafficSignalMsg sig;
  sig.x               = static_cast<float>( world_xy_demo_signal.first );
  sig.y               = static_cast<float>( world_xy_demo_signal.second );
  sig.signal_group_id = 1; // constant for demo
  sig.state           = TrafficSignalMsg::RED;

  out.signals.clear();
  out.signals.push_back( sig );

  publisher_traffic_signals->publish( out );
  RCLCPP_DEBUG( get_logger(), "Published RED at (%.2f, %.2f)", sig.x, sig.y );
}

} // namespace adore

int
main( int argc, char** argv )
{
  rclcpp::init( argc, argv );
  rclcpp::spin( std::make_shared<adore::VisionInterface>() );
  rclcpp::shutdown();
  return 0;
}