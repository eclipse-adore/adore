#include <iostream>
#include <vector>
#include <string>
#include <iomanip>
#include <chrono>
#include <optional>
#include "adore_map/lat_long_conversions.hpp"

void printLatLongToUTMCPP(const std::string& city, double lat, double lon) {
    std::chrono::time_point<std::chrono::high_resolution_clock> start, end;
    std::chrono::duration<double, std::milli> duration_ms;

    start = std::chrono::high_resolution_clock::now();
    std::optional<std::vector<double>> utmOptional = adore::map::convert_lat_lon_to_utm(lat, lon);
    end = std::chrono::high_resolution_clock::now();
    duration_ms = end - start;

    if (!utmOptional.has_value()) {
        std::cout << city << "\n    Error: Failed to convert LatLong to UTM" << std::endl;
        return;
    }
    
    std::vector<double> utmResult = utmOptional.value();
    std::cout << std::fixed << std::setprecision(6);
    std::cout << city << "\n    LatLong: (" << lat << ", " << lon << ") -> UTM: (" 
              << utmResult[0] << ", " << utmResult[1] << "), Zone: " << static_cast<int>(utmResult[2])
              << ", UTM zone letter: " << static_cast<char>(utmResult[3])
              << " [execution time: " << duration_ms.count() << " ms]" << std::endl;

    start = std::chrono::high_resolution_clock::now();
    std::optional<std::vector<double>> latLongOptional = adore::map::convert_utm_to_lat_lon(utmResult[0], utmResult[1], static_cast<int>(utmResult[2]), std::string(1, static_cast<char>(utmResult[3])));
    end = std::chrono::high_resolution_clock::now();
    duration_ms = end - start;

    if (!latLongOptional.has_value()) {
        std::cout << "    Error: Failed to convert UTM to LatLong" << std::endl;
        return;
    }
    
    std::vector<double> latLongResult = latLongOptional.value();
    std::cout << "    UTM: (" << utmResult[0] << ", " << utmResult[1] << "), Zone: " << static_cast<int>(utmResult[2])
              << ", UTM zone letter: " << static_cast<char>(utmResult[3]) << " -> LatLong: (" 
              << latLongResult[0] << ", " << latLongResult[1] << ")"
              << " [execution time: " << duration_ms.count() << " ms]" << std::endl;
}

void printLatLongToUTMPython(const std::string& city, double lat, double lon) {
    std::chrono::time_point<std::chrono::high_resolution_clock> start, end;
    std::chrono::duration<double, std::milli> duration_ms;

    start = std::chrono::high_resolution_clock::now();
    std::optional<std::vector<double>> utmOptional = adore::map::convert_lat_lon_to_utm_python(lat, lon);
    end = std::chrono::high_resolution_clock::now();
    duration_ms = end - start;

    if (!utmOptional.has_value()) {
        std::cout << city << "\n    Error: Failed to convert LatLong to UTM" << std::endl;
        return;
    }
    
    std::vector<double> utmResult = utmOptional.value();
    std::cout << std::fixed << std::setprecision(6);
    std::cout << city << "\n    LatLong: (" << lat << ", " << lon << ") -> UTM: (" 
              << utmResult[0] << ", " << utmResult[1] << "), Zone: " << static_cast<int>(utmResult[2])
              << ", UTM zone letter: " << static_cast<char>(utmResult[3])
              << " [execution time: " << duration_ms.count() << " ms]" << std::endl;

    start = std::chrono::high_resolution_clock::now();
    std::optional<std::vector<double>> latLongOptional = adore::map::convert_utm_to_lat_lon_python(utmResult[0], utmResult[1], static_cast<int>(utmResult[2]), std::string(1, static_cast<char>(utmResult[3])));
    end = std::chrono::high_resolution_clock::now();
    duration_ms = end - start;

    if (!latLongOptional.has_value()) {
        std::cout << "    Error: Failed to convert UTM to LatLong" << std::endl;
        return;
    }
    
    std::vector<double> latLongResult = latLongOptional.value();
    std::cout << "    UTM: (" << utmResult[0] << ", " << utmResult[1] << "), Zone: " << static_cast<int>(utmResult[2])
              << ", UTM zone letter: " << static_cast<char>(utmResult[3]) << " -> LatLong: (" 
              << latLongResult[0] << ", " << latLongResult[1] << ")"
              << " [execution time: " << duration_ms.count() << " ms]" << std::endl;
}

int main() {
    double lat1 = 37.7749, lon1 = -122.4194;
    double lat2 = 34.0522, lon2 = -118.2437;
    double lat3 = 52.5200, lon3 = 13.4050;
    double lat4 = -26.2041, lon4 = 28.0473;

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
