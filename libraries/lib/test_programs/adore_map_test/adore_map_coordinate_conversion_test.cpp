#include <iostream>
#include <vector>
#include <string>
#include <iomanip>
#include <chrono> // For timing
#include "adore_map/lat_long_conversions.hpp"

void printLatLongToUTMCPP(const std::string& city, double lat, double lon) {
    std::chrono::time_point<std::chrono::high_resolution_clock> start, end;
    std::chrono::duration<double, std::milli> duration_ms;

    start = std::chrono::high_resolution_clock::now();
    std::vector<double> utmResult = adore::map::convert_lat_lon_to_utm(lat, lon);
    end = std::chrono::high_resolution_clock::now();
    duration_ms = end - start;

    std::cout << std::fixed << std::setprecision(6);
    std::cout << city << "\n    LatLong: (" << lat << ", " << lon << ") -> UTM: (" 
              << utmResult[0] << ", " << utmResult[1] << "), Zone: " << static_cast<int>(utmResult[2])
              << ", UTM zone letter: " << static_cast<char>(utmResult[3])
              << " [execution time: " << duration_ms.count() << " ms]" << std::endl;

    start = std::chrono::high_resolution_clock::now();
    std::vector<double> latLongResult = adore::map::convert_utm_to_lat_lon(utmResult[0], utmResult[1], static_cast<int>(utmResult[2]), std::string(1, static_cast<char>(utmResult[3])));
    end = std::chrono::high_resolution_clock::now();
    duration_ms = end - start;

    std::cout << "    UTM: (" << utmResult[0] << ", " << utmResult[1] << "), Zone: " << static_cast<int>(utmResult[2])
              << ", UTM zone letter: " << static_cast<char>(utmResult[3]) << " -> LatLong: (" 
              << latLongResult[0] << ", " << latLongResult[1] << ")"
              << " [exeution time: " << duration_ms.count() << " ms]" << std::endl;
}

void printLatLongToUTMPython(const std::string& city, double lat, double lon) {
    std::chrono::time_point<std::chrono::high_resolution_clock> start, end;
    std::chrono::duration<double, std::milli> duration_ms;

    start = std::chrono::high_resolution_clock::now();
    std::vector<double> utmResult = adore::map::convert_lat_lon_to_utm_python(lat, lon);
    end = std::chrono::high_resolution_clock::now();
    duration_ms = end - start;

    std::cout << std::fixed << std::setprecision(6);
    std::cout << city << "\n    LatLong: (" << lat << ", " << lon << ") -> UTM: (" 
              << utmResult[0] << ", " << utmResult[1] << "), Zone: " << static_cast<int>(utmResult[2])
              << ", UTM zone letter: " << static_cast<char>(utmResult[3])
              << " [execution time: " << duration_ms.count() << " ms]" << std::endl;

    start = std::chrono::high_resolution_clock::now();
    std::vector<double> latLongResult = adore::map::convert_utm_to_lat_lon_python(utmResult[0], utmResult[1], static_cast<int>(utmResult[2]), std::string(1, static_cast<char>(utmResult[3])));
    end = std::chrono::high_resolution_clock::now();
    duration_ms = end - start;

    std::cout << "    UTM: (" << utmResult[0] << ", " << utmResult[1] << "), Zone: " << static_cast<int>(utmResult[2])
              << ", UTM zone letter: " << static_cast<char>(utmResult[3]) << " -> LatLong: (" 
              << latLongResult[0] << ", " << latLongResult[1] << ")"
              << " [exeution time: " << duration_ms.count() << " ms]" << std::endl;
}

int main() {
    double lat1 = 37.7749, lon1 = -122.4194; // San Francisco, CA
    double lat2 = 34.0522, lon2 = -118.2437; // Los Angeles, CA
    double lat3 = 52.5200, lon3 = 13.4050;   // Berlin, Germany
    double lat4 = -26.2041, lon4 = 28.0473;  // Johannesburg, South Africa

    std::cout << "LatLong to UTM and back to LatLong:" << std::endl;
   
    std::cout << "  CPP:" << std::endl; 
    printLatLongToUTMCPP("  San Francisco, CA", lat1, lon1);
    std::cout << "  Python:" << std::endl; 
    printLatLongToUTMPython("  San Francisco, CA", lat1, lon1);
   
    std::cout << std::endl; 
    std::cout << "  CPP:" << std::endl; 
    printLatLongToUTMCPP("  Los Angeles, CA", lat2, lon2);
    std::cout << "  Python:" << std::endl; 
    printLatLongToUTMPython("  Los Angeles, CA", lat2, lon2);
   
    std::cout << std::endl; 
    std::cout << "  CPP:" << std::endl; 
    printLatLongToUTMCPP("  Berlin, Germany", lat3, lon3);
    std::cout << "  Python:" << std::endl; 
    printLatLongToUTMPython("  Berlin, Germany", lat3, lon3);

    std::cout << std::endl; 
    std::cout << "  CPP:" << std::endl; 
    printLatLongToUTMCPP("  Johannesburg, South Africa", lat4, lon4);
    std::cout << "  Python:" << std::endl; 
    printLatLongToUTMPython("  Johannesburg, South Africa", lat4, lon4);

    return 0;
}

