/********************************************************************************
 * Copyright (c) 2026 Contributors to the Eclipse Foundation
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

#include <cstddef>
#include <cstdlib>
#include <iostream>
#include <string>
#include <vector>

#include "adore_tridap/helpers.hpp"
#include "adore_tridap/weather_forecast_downloader.hpp"

#include <nlohmann/json.hpp>

using namespace adore::tridap;

namespace
{
// Structural validation of a forecast, mirroring HourlyEntry / WeatherForecast.
bool
validate( nlohmann::json& forecast, const std::string& module_name )
{
  const std::string              expected_source      = forecast.at( "source" ).get<std::string>();
  const std::vector<std::string> required_hourly_keys = {
    "time_iso",       "temperature_c",      "apparent_temperature_c", "precipitation_mm", "precipitation_probability_pct",
    "wind_speed_kmh", "wind_direction_deg", "wind_gusts_kmh",         "cloud_cover_pct",  "visibility_m",
    "weather_code",   "weather_description"
  };

  if( !forecast.contains( "source" ) || !forecast.contains( "latitude" ) || !forecast.contains( "longitude" )
      || !forecast.contains( "fetch_time_unix" ) || !forecast.contains( "valid_until_unix" ) || !forecast.contains( "timezone" )
      || !forecast.contains( "hourly" ) )
  {
    std::cerr << module_name << ": Result is missing a required top-level field." << std::endl;
    return false;
  }
  if( !forecast.at( "hourly" ).is_array() || forecast.at( "hourly" ).empty() )
  {
    std::cerr << module_name << ": 'hourly' array is empty or invalid." << std::endl;
    return false;
  }
  const double fetch_time  = forecast.at( "fetch_time_unix" ).get<double>();
  const double valid_until = forecast.at( "valid_until_unix" ).get<double>();
  if( !( valid_until >= fetch_time ) )
  {
    std::cerr << module_name << ": 'valid_until_unix' (" << valid_until << ") is earlier than 'fetch_time_unix' (" << fetch_time << ")."
              << std::endl;
    return false;
  }
  for( const auto& entry : forecast.at( "hourly" ) )
  {
    for( const auto& key : required_hourly_keys )
    {
      if( !entry.contains( key ) )
      {
        std::cerr << module_name << ": 'hourly' entry is missing required field '" << key << "'." << std::endl;
        return false;
      }
    }
  }

  std::cout << module_name << ": Source '" << expected_source << "' returned a valid forecast (" << forecast.at( "hourly" ).size()
            << " hourly entries)." << std::endl;
  return true;
} // end validate
} // end namespace

// Main function
int
main( int argc, char* argv[] )
{
  // Test position for Berlin
  double lat_for_berlin = 52.52;
  double lon_for_berlin = 13.405;
  // Test position for Washington, D.C.
  double lat_for_washington_dc = 38.8977;
  double lon_for_washington_dc = -77.0365;

  // Initialize the configuration from a JSON config file (mirrors the Python
  // build_source_chain(): sources keep fixed order noaa, dwd, open_meteo,
  // enabled ones are kept, then sorted by ascending priority).
  ConfigWeatherForecastDownloader cfg( "../../../src/adore_test_programs/adore_weather_forecast_downloader_test/config/"
                                       "weather_forecast_downloader_test_config.json" );

  // Since this test program is standalone, we can let the internal curl wrapper initialize
  // (curl_global_init = true) and later, upon leaving scope, also cleanup cURL globally
  // (curl_global_cleanup = true).
  WeatherForecastDownloader weather_forecast_downloader( cfg, /*curl_global_init=*/true,
                                                         /*curl_global_cleanup=*/true, /*debug_mode=*/true );

  nlohmann::json forecast;

  if( !weather_forecast_downloader.is_initialized() )
  {
    std::cerr << module_name( argv[0] ) << ": Could not initialize the HTTP client." << std::endl;
    return -1;
  }

  const std::vector<std::pair<std::string, WeatherSourceConfig>> source_chain = cfg.build_source_chain();
  if( source_chain.empty() )
  {
    std::cerr << module_name( argv[0] ) << ": No enabled sources configured." << std::endl;
    return -1;
  }

  // Print the evaluation order that will be tried (first enabled source wins).
  std::cout << module_name( argv[0] ) << ": Source chain (first success wins): ";
  for( std::size_t i = 0; i < source_chain.size(); ++i )
  {
    if( i > 0 )
      std::cout << ", ";
    std::cout << source_chain[i].first << " (priority " << source_chain[i].second.priority << ")";
  }
  std::cout << std::endl;

  // Primary test: run the configured source chain and let the first enabled source win,
  // exactly like the Python weather_service_interface source chain.
  std::cout << module_name( argv[0] ) << ": Querying weather forecast for Berlin (lat=" << lat_for_berlin << ", lon=" << lon_for_berlin
            << "). Should succeed for DWD. Would fail for NOAA, but first one wins -> NOAA is skipped." << std::endl;
  // First test with the coordinates of Berlin (should succeed for DWD.
  // Would fail for NOAA, but first one wins -> NOAA is skipped)
  if( !weather_forecast_downloader.download( lat_for_berlin, lon_for_berlin ) )
  {
    std::cerr << module_name( argv[0] ) << ": download() failed for all configured sources." << std::endl;
    return -1;
  }
  forecast = weather_forecast_downloader.get_json_data();
  // validation of the winning forecast
  if( !validate( forecast, argv[0] ) )
  {
    return -1;
  }

  // Next test with the coordinates of Washington, D.C. (should fail for DWD)
  std::cout << module_name( argv[0] ) << ": Querying weather forecast for Washington, D.C. (lat=" << lat_for_washington_dc
            << ", lon=" << lon_for_washington_dc << "). Should fail for DWD and succeed for NOAA." << std::endl;
  if( !weather_forecast_downloader.download( lat_for_washington_dc, lon_for_washington_dc ) )
  {
    std::cerr << module_name( argv[0] ) << ": download() failed for all configured sources." << std::endl;
    return -1;
  }
  forecast = weather_forecast_downloader.get_json_data();
  // validation of the winning forecast
  if( !validate( forecast, argv[0] ) )
  {
    return -1;
  }

  // Secondary test: independently exercise every configured source against its live API,
  // so that all endpoints (noaa, dwd, open_meteo) are validated individually.
  // First test with the coordinates of Berlin (should fail for NOAA)
  for( const auto& source_entry : source_chain )
  {
    const std::string& source_name = source_entry.first;
    std::cout << module_name( argv[0] ) << ": Testing source '" << source_name << "' individually..." << std::endl;
    std::cout << module_name( argv[0] ) << ": Querying weather forecast for Berlin (lat=" << lat_for_berlin << ", lon=" << lon_for_berlin
              << "). Should fail for NOAA." << std::endl;
    if( !weather_forecast_downloader.download_from( source_name, lat_for_berlin, lon_for_berlin ) )
    {
      // A single source being temporarily unavailable must not fail the whole test,
      // as long as at least one source (the chain test above) already succeeded.
      std::cerr << module_name( argv[0] ) << ": Source '" << source_name
                << "' is not reachable right now (skipped; at least one source succeeded)." << std::endl;
      continue;
    }
    if( weather_forecast_downloader.get_json_data().at( "source" ) != source_name )
    {
      std::cerr << module_name( argv[0] ) << ": Source mismatch for '" << source_name << "'." << std::endl;
      return -1;
    }
    std::cout << module_name( argv[0] ) << ": Source '" << source_name << "' returned a valid forecast ("
              << weather_forecast_downloader.get_json_data().at( "hourly" ).size() << " hourly entries)." << std::endl;
  }

  // Next test with the coordinates of Washington, D.C. (should fail for DWD)
  for( const auto& source_entry : source_chain )
  {
    const std::string& source_name = source_entry.first;
    std::cout << module_name( argv[0] ) << ": Testing source '" << source_name << "' individually..." << std::endl;
    std::cout << module_name( argv[0] ) << ": Querying weather forecast for Washington, D.C. (lat=" << lat_for_washington_dc
              << ", lon=" << lon_for_washington_dc << "). Should fail for DWD." << std::endl;
    if( !weather_forecast_downloader.download_from( source_name, lat_for_washington_dc, lon_for_washington_dc ) )
    {
      // A single source being temporarily unavailable must not fail the whole test,
      // as long as at least one source (the chain test above) already succeeded.
      std::cerr << module_name( argv[0] ) << ": Source '" << source_name
                << "' is not reachable right now (skipped; at least one source succeeded)." << std::endl;
      continue;
    }
    if( weather_forecast_downloader.get_json_data().at( "source" ) != source_name )
    {
      std::cerr << module_name( argv[0] ) << ": Source mismatch for '" << source_name << "'." << std::endl;
      return -1;
    }
    std::cout << module_name( argv[0] ) << ": Source '" << source_name << "' returned a valid forecast ("
              << weather_forecast_downloader.get_json_data().at( "hourly" ).size() << " hourly entries)." << std::endl;
  }

  std::cout << module_name( argv[0] ) << ": Weather forecast downloader query test completed successfully, good!" << std::endl << std::endl;
  return 0;
}
