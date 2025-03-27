#ifndef JSON_H
#define JSON_H

#include <nlohmann/json.hpp>
#include <unordered_map>
#include <string>
#include <any>
#include <vector>
#include <memory>

// Typedefs for our multidimensional map representation
using JsonMap = std::unordered_map<std::string, std::any>;
using JsonArray = std::vector<std::any>;

// Function declarations
JsonMap from_json(const nlohmann::json& j);
nlohmann::json to_json(const JsonMap& map);

// Helper functions
std::any json_value_to_any(const nlohmann::json& j);
nlohmann::json any_to_json_value(const std::any& value);

#endif // JSON_H
