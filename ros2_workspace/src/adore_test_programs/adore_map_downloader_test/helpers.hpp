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

#pragma once
#include <iostream>
#include <string>

/** @brief Helper function to extract module name from the path of the executable
 * @param path The full path of the executable
 * @return The module name extracted from the path 
 */
std::string module_name( const char* path )
{
  if( path == nullptr )
  {
    return "";
  }
  std::string full_path( path );
  std::string::size_type i = full_path.find_last_of( "/\\" );
  if( i != std::string::npos )
  {
    std::string name( full_path.substr( i + 1 ) );
    return name;

  }
  return full_path;
}

/** @brief Modifies a filename by replacing the last dot with an underscore and appending a new end withsuffix
 * @param filename The original filename
 * @param new_end_with_suffix The new end with suffix to append
 * @return The modified filename
 */
std::string modified_filename( const std::string filename, const std::string new_end_with_suffix ) 
{
  std::string str = filename;
  size_t last_dot_pos = str.find_last_of( '.' );
  if( last_dot_pos != std::string::npos )
  {
    str[ last_dot_pos ] = '_';
  }
  std::string modified_filename = str + new_end_with_suffix;
  return modified_filename;
}

/** @brief Compares two files for identical content
 * @param file1 The path to the first file
 * @param file2 The path to the second file
 * @return true if the files are identical, false otherwise
 */
bool are_identical_files( const std::string& file1, const std::string& file2 )
{
  // If under linux, call diff -a, if under windows, call fc
  // to compare the two JSON files
  #ifdef _WIN32
    std::string command = "fc \"" + file1 + "\" \"" + file2 + "\"";
  #else
    std::string command = "diff -a \"" + file1 + "\" \"" + file2 + "\"";
  #endif
  int ret = system( command.c_str() );
  return ret == 0;
}
