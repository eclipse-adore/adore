#include <iostream>
#include "adore_tridap/nowcast.hpp"
#include "adore_tridap/helpers.hpp"

using namespace adore::tridap;

// Main function
int main( int argc, char* argv[] )
{
  if( argc != 1 )
  {
    std::cerr << "Usage: " << module_name( argv[0] ) << " (i.e., without parameters)." << std::endl;
    exit( -1 );
  }

  // Clean up potential cache remnants from previous test runs
  std::filesystem::remove_all( "cache" ); 

  // Initialize the configuration from a properties file
  ConfigNowcast cfg( "../../../src/adore_test_programs/adore_nowcast_test/config/nowcast_test_config.json" );
  // Use current directory for file cache and enable debug mode
  Nowcast nowcast( cfg.server_url, cfg.username, cfg.password, cfg.project_name, cfg.target_srs, 
    cfg.bbox, cfg.layer_name_nowcast, "", true, true, true ); // curl_global_init, curl_global_cleanup, debug: 
                                      // Since this test program is standalone, we can let the internal 
                                      // curl wrapper initialize, and later upon leaving scope, also 
                                      // cleanup curl globally

  // First test the now() method to get the current time in ISO 8601 format
  std::string current_time = Nowcast::now( true );
  std::cout << module_name( argv[0] ) << ": Current time in ISO 8601 format: " << current_time << std::endl; 

  std::string test_time = "2019-08-02T18:00:00.000Z";
  double thunderstorm_probability = nowcast.query( test_time );
  std::cout << module_name( argv[0] ) << ": Thunderstorm probability for " << test_time << ": " 
    << std::setprecision(17) << thunderstorm_probability << std::endl;
  if( thunderstorm_probability < 0.0 )
  {
    std::cerr << module_name( argv[0] ) << ": Nowcast query failed for time " << test_time << std::endl;
    exit( -1 );
  } else if( thunderstorm_probability > 1.0 )
  {
    std::cerr << module_name( argv[0] ) << ": Nowcast query returned invalid probability value " 
      << thunderstorm_probability << " for time " << test_time << std::endl;
    exit( -1 );
  } else if( thunderstorm_probability != 0.0016004316275939345 )
  {
    std::cerr << module_name( argv[0] ) << ": Nowcast query returned unexpected probability value " 
      << thunderstorm_probability << " for time " << test_time << std::endl;
    exit( -1 );
  } 
  std::cout << module_name( argv[0] ) << ": Nowcast query returned expected probability value " 
    << thunderstorm_probability << " for time " << test_time << std::endl;
  std::cout << module_name( argv[0] ) << ": Nowcast query test completed successfully, good!" 
    << std::endl << std::endl;
  return 0;
}