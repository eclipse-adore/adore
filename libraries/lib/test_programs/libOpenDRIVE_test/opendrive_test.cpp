#include <iostream>

#include "Lane.h"
#include "OpenDriveMap.h"

int
main()
{
  std::cerr << "opendrive map test" << std::endl;
  auto key = odr::LaneKey( "1", 0.0, 0 );
  std::cerr << key.road_id << std::endl;
  return 0;
}