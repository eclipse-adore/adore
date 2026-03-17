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
#include "adore_map/map_loader.hpp"
#include "adore_map/config.hpp"
#include "helpers.hpp"

/**
 * @brief Test program to load R2S map data from WFS and compare with R2S map data loaded from file
 * @details This program initializes a MapDownloader instance, downloads map data for reference lines and 
 *          lane borders from WFS, loads R2S map data from from CSV files created using a Python downloader 
 *          and the R2S parser (the legacy methods for loading map data) and compares the two datasets for 
 *          equality. These files were created from the same source as the WFS data, so they should match. 
 *          It demonstrates the functionality of loading map data from WFS and ensures consistency with 
 *          legacy R2S CSV files. The program uses a configuration file to set parameters such as server URL, 
 *          project name, layer names, and bounding box.
 * @return int Exit code indicating success or failure
 */

// Main function to test loading R2S map data from WFS and comparing with R2S map data loaded from file
int main( int argc, char* argv[] )
{
  if( argc != 1 )
  {
    std::cerr << "Usage: " << module_name( argv[0] ) << " (i.e., without parameters)." << std::endl;
    exit( -1 );
  }

   // Clean up potential remnants from previous test runs: remove the complete cache directory, which may contain cached map layer data from previous runs.
  std::filesystem::remove_all( "cache" ); 

  Config cfg( "../../../../adore_test_programs/adore_map_downloader_test/config/r2s_wfs_config_bs.json" );
  MapDownloader map_downloader( cfg );

  // Replace above line by the next two lines to enable debug mode:
  // MapDownloader map_downloader( cfg.server_url, cfg.username, cfg.password, cfg.project_name, cfg.target_srs, cfg.bbox,
  //   "", false, false, true );
  
  // For this test, disable caching of map layer data in the MapCache instance (caching is already tested in adore_map/test/map_download_cache_test.cpp)
  map_downloader.turn_off_cache(); 
  
  // For testing purposes, curl_global_init, curl_global_cleanup, and debug_mode all set to false here. 
  // This means that the internal curl wrapper will not initialize or cleanup curl globally
  // and debug mode is off. 
  // Since this is a standalone test program, global curl initialization relies on the fact that the 
  // first call to curl_easy_init() invokes it internally (this works, but is not recommended for production code). 
  // Global curl cleanup relies on the C++ runtime system and the OS to clean up resources upon program 
  // exit. In a real application, the aforementioned flags should be set according to the application's needs.

  std::cout << module_name( argv[0] ) << ": A) Loading r2s map data from file... " << std::endl;
  std::cout << module_name( argv[0] ) << ": 1. Loading road file..." << std::endl;
  auto border_data_r2sr_from_file = adore::r2s::load_border_data_from_r2sr_file( "../../../../adore_test_programs/adore_map_downloader_test/csv/de_bs_borders_wfs.r2sr" );
  std::cout << module_name( argv[0] ) << ": Road file has been loaded, size: " << border_data_r2sr_from_file.size() 
    << std::endl;
  std::cout << module_name( argv[0] ) << ": 2. Lane file..." << std::endl;
  // The same path as before is passed to the next method, since the method will change the suffix to .r2sl internally 
  auto border_data_r2sl_from_file = adore::r2s::load_border_data_from_r2sl_file( "../../../../adore_test_programs/adore_map_downloader_test/csv/de_bs_borders_wfs.r2sr" );
  std::cout << module_name( argv[0] ) << ": Lane file has been loaded, size: " << border_data_r2sl_from_file.size() << std::endl;

  std::cout << module_name( argv[0] ) << ": B) Loading r2s map data from WFS... " << std::endl;
  std::cout << module_name( argv[0] ) << ": 1. Loading reference lines from WFS... (layer name: " 
    << cfg.layer_name_reference_lines << ")" << std::endl;
  auto border_data_r2sr_from_wfs = adore::r2s::download_reference_lines( map_downloader, cfg.layer_name_reference_lines );
  std::cout << module_name( argv[0] ) << ": Reference lines have been loaded from WFS, size: " 
    << border_data_r2sr_from_wfs.size() << std::endl;
  std::cout << module_name( argv[0] ) << ": 2. Loading lane borders from WFS... (layer name: " 
    << cfg.layer_name_lane_borders << ")" << std::endl;
  auto border_data_r2sl_from_wfs = adore::r2s::download_lane_borders( map_downloader, cfg.layer_name_lane_borders );
  std::cout << module_name( argv[0] ) << ": Lane borders have been loaded from WFS, size: " 
    << border_data_r2sl_from_wfs.size() << std::endl;
    
  std::cout << module_name( argv[0] ) << ": Comparing the border data... " << std::endl;
  if ( border_data_r2sr_from_file != border_data_r2sr_from_wfs ) {
    std::cerr << module_name( argv[0] ) << ": R2SR border data from file and WFS differ, test failed." << std::endl;
    return -2;
  }
  if ( border_data_r2sl_from_file != border_data_r2sl_from_wfs ) {
    std::cerr << module_name( argv[0] ) << ": R2SL border data from file and WFS differ, test failed." << std::endl;
    return -2;
  }
  std::cout << module_name( argv[0] ) << ": Tolerating differences up to 2e-6, border data from file and WFS are identical. Test succeeded." 
    << std::endl;
  return 0;
}
