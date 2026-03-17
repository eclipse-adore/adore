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

#include <iostream>
#include <string>
#include <curl/curl.h>
#include <filesystem>
#include "adore_map/map_downloader.hpp"
#include "adore_map/config.hpp"
#include "helpers.hpp"

/**
 * @brief Test program to download map data from WFS and save as JSON files
 * @details This program initializes a MapDownloader instance, downloads map layer data for reference lines and lane borders,
 *          and saves the data as JSON files. It demonstrates both simple and flexible methods for downloading map layer data.
 *          The program uses a configuration file to set parameters such as server URL, project name, layer names, and bounding box.
 *          A map cache is used to optimize repeated requests.
 * @return int Exit code indicating success or failure
 */

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
  Config cfg( "../../../../adore_test_programs/adore_map_downloader_test/config/r2s_wfs_config_bs.json" );
  // Use current directory for file cache and enable debug mode
  MapDownloader map_downloader( cfg.server_url, cfg.username, cfg.password, cfg.project_name, cfg.target_srs, 
    cfg.bbox, "", true, true, true ); // curl_global_init, curl_global_cleanup, debug: 
                                      // Since this test program is standalone, we can let the internal 
                                      // curl wrapper initialize, and later upon leaving scope, also 
                                      // cleanup curl globally

  // This test first performs an actual WFS download w/o resorting to loading of cached content 
  // (the latter is already tested in adore_map/test/map_download_cache_test.cpp)
  // First test the simple methods with less parameters

   // Debugging line to see the start of the simple methods
  std::cout << module_name( argv[0] ) << ": Starting test of simple methods..." << std::endl;

  // Load the first map layer as JSON: layer name is that for reference lines
  if( !map_downloader.download( cfg.layer_name_reference_lines, cfg.bbox ) ) { 
    std::cerr << module_name( argv[0] ) << ": Failed to load map layer." << std::endl;
    return -1;
  }

  // Pretty print the reference line JSON data
  std::cout << module_name( argv[0] ) << ": Reference Line Data:" << std::endl;
  map_downloader.pretty_print();
  
  // Create a JSON file for reference lines
  map_downloader.save( cfg.reference_line_filename );
  std::cout << module_name( argv[0] ) << ": JSON file with reference line data created successfully." << std::endl;

  // Load a second map layer as JSON: lane borders
  // This is another WFS request to obtain the lane border data for the UrbanDrive project
  // The same internal cURL handle will be used to perform this request 
  // So there is no need to reinitialize cURL
  // The response will again be in JSON format, which we will parse and save to a file

  // Now layer name is that for lane borders
  if( !map_downloader.download( cfg.layer_name_lane_borders, cfg.bbox ) ) { 
    std::cerr << module_name( argv[0] ) << ": Failed to load map layer." << std::endl;
    return -1;
  }

  // Pretty print the lane border JSON data
  std::cout << module_name( argv[0] ) << ": Lane Border Data:" << std::endl;
  map_downloader.pretty_print();

  // Create a JSON file for lane borders
  map_downloader.save( cfg.lane_border_filename );
  std::cout << module_name( argv[0] ) << ": JSON file with lane border data created successfully." << std::endl;

  // Now test the flexible methods with more parameters
  // Since the map cache is active, the following download calls hit the cache and do not perform another WFS request. 
  // Still we can test that the flexible methods with more parameters work correctly.
  // Debugging line to see the start of the flexible methods
  std::cout << module_name( argv[0] ) << ": Starting test of flexible methods with more parameters..." << std::endl;

  // Load the first map layer as JSON: reference lines
  // It is important that the map cache is active, so that the following download call hits the cache and does not perform 
  // another WFS request. That way, the subsequent tests can expect the same JSON data as before (in particular, w/ identical time stamps), 
  // which is important for the file comparison tests.
  assert( map_downloader.is_cache_active() == true );

  if( !map_downloader.download( cfg.server_url, cfg.project_name, cfg.target_srs,
      cfg.layer_name_reference_lines, cfg.bbox ) )
  {
    std::cerr << module_name( argv[0] ) << ": Failed to load reference line map layer." << std::endl;
    return -1;
  }

  // Get the parsed JSON data for reference lines
  nlohmann::json& reference_line_data = map_downloader.get_json_data();

  // Pretty print the reference line JSON data
  std::cout << module_name( argv[0] ) << ": Reference Line Data:" << std::endl;
  map_downloader.pretty_print( reference_line_data );

  // Create a JSON file for reference lines
  std::string reference_line_downloaded_with_flexible_method_filename 
    = modified_filename( cfg.reference_line_filename, "_downloaded_with_flexible_method.json" );
  map_downloader.save( reference_line_data, reference_line_downloaded_with_flexible_method_filename );
  std::cout << module_name( argv[0] ) << ": Another JSON file with reference line data successfully created with flexible method." << std::endl;

  if( are_identical_files( cfg.reference_line_filename, reference_line_downloaded_with_flexible_method_filename ) )
  {
    std::cout << module_name( argv[0] ) << ": The two JSON files for reference lines (from the simple and the flexible method) are identical, good." << std::endl;
  }
  else
  {
    std::cout << module_name( argv[0] ) << ": The two JSON files for reference lines (from the simple and the flexible method) differ." << std::endl;
    return -1; // Return error code if files differ
  }
  
  // Load the map layer from file instead of downloading it: reference lines
  map_downloader.load( cfg.reference_line_filename, reference_line_data );
  std::cout << module_name( argv[0] ) << ": Reference line map layer loaded from file: " << cfg.reference_line_filename << std::endl;

  // Save again as JSON file for reference lines
  std::string reference_line_loaded_filename = modified_filename( cfg.reference_line_filename, "_loaded.json" );
  map_downloader.save( reference_line_data, reference_line_loaded_filename );
  std::cout << module_name( argv[0] ) << ": Another JSON file with reference line data successfully created by loading and saving." 
    << std::endl;

  if( are_identical_files( cfg.reference_line_filename, reference_line_loaded_filename ) )
  {
    std::cout << module_name( argv[0] ) << ": The two JSON files for reference lines (from the simple method and from loading and saving) are identical, good." << std::endl;
  }
  else
  {
    std::cout << module_name( argv[0] ) << ": The two JSON files for reference lines (from the simple method and from loading and saving) differ." << std::endl;
    return -1; // Return error code if files differ
  }
  // clean up: remove the created JSON files for reference lines
  std::remove( cfg.reference_line_filename.c_str() );
  std::remove( reference_line_loaded_filename.c_str() );
  std::remove( reference_line_downloaded_with_flexible_method_filename.c_str() );

  // Load another map layer as JSON: lane borders
  // Again, it is important that the map cache is active, so that the following download call hits the cache and does not perform 
  // another WFS request. That way, the subsequent tests can expect the same JSON data as before (in particular, w/ identical time stamps), 
  // which is important for the file comparison tests.
  if( !map_downloader.download( cfg.server_url, cfg.project_name, cfg.target_srs,
      cfg.layer_name_lane_borders, cfg.bbox ) )
  {
    std::cerr << module_name( argv[0] ) << ": Failed to load lane border map layer." << std::endl;
    return -1;
  }

  // Get the parsed JSON data for lane borders
  nlohmann::json& lane_border_data = map_downloader.get_json_data();

  // Pretty print the lane border JSON data
  map_downloader.pretty_print( lane_border_data );

  // Create a JSON file for lane borders
  std::string lane_border_downloaded_with_flexible_method_filename 
    = modified_filename( cfg.lane_border_filename, "_downloaded_with_flexible_method.json" );
  map_downloader.save( lane_border_data, lane_border_downloaded_with_flexible_method_filename );
  std::cout << module_name( argv[0] ) << ": Another JSON file with lane border data successfully created with flexible method." << std::endl;

  if( are_identical_files( cfg.lane_border_filename, lane_border_downloaded_with_flexible_method_filename ) )
  {
    std::cout << module_name( argv[0] ) << ": The two JSON files for lane borders (from the simple and the flexible method) are identical, good." << std::endl;
  }
  else
  {
    std::cout << module_name( argv[0] ) << ": The two JSON files for lane borders (from the simple and the flexible method) differ." << std::endl;
    return -1; // Return error code if files differ
  }

  // Load the map layer from file instead of downloading it: lane borders
  map_downloader.load( cfg.lane_border_filename, lane_border_data );
  std::cout << module_name( argv[0] ) << ": Lane border map layer loaded from file: " << cfg.lane_border_filename << std::endl;

  // Save again as JSON file for lane borders
  std::string lane_border_loaded_filename = modified_filename( cfg.lane_border_filename, "_loaded.json" );
  map_downloader.save( lane_border_data, lane_border_loaded_filename );
  std::cout << module_name( argv[0] ) << ": Another JSON file with lane border data successfully created by loading and saving." << std::endl;

  if( are_identical_files( cfg.lane_border_filename, lane_border_loaded_filename ) )
  {
    std::cout << module_name( argv[0] ) << ": The two JSON files for lane borders (from the simple method and from loading and saving) are identical, good." << std::endl;
  } 
  else
  {
    std::cout << module_name( argv[0] ) << ": The two JSON files for lane borders (from the simple method and from loading and saving) differ." << std::endl;
    return -1; // Return error code if files differ
  }

  // Clean up: remove the created JSON files for lane borders
  std::remove( cfg.lane_border_filename.c_str() );
  std::remove( lane_border_loaded_filename.c_str() );
  std::remove( lane_border_downloaded_with_flexible_method_filename.c_str() );

  return 0; // Return success code
}
