#include "adore_util/json.h"
#include <iostream>

JsonMap from_json(const nlohmann::json& j) {
    JsonMap result;
    
    if (!j.is_object()) {
        throw std::runtime_error("Root JSON value must be an object");
    }
    
    for (auto it = j.begin(); it != j.end(); ++it) {
        result[it.key()] = json_value_to_any(it.value());
    }
    
    return result;
}

std::any json_value_to_any(const nlohmann::json& j) {
    if (j.is_null()) {
        return nullptr;
    }
    else if (j.is_boolean()) {
        return j.get<bool>();
    }
    else if (j.is_number_integer()) {
        return j.get<int64_t>();
    }
    else if (j.is_number_float()) {
        return j.get<double>();
    }
    else if (j.is_string()) {
        return j.get<std::string>();
    }
    else if (j.is_array()) {
        JsonArray array;
        for (const auto& element : j) {
            array.push_back(json_value_to_any(element));
        }
        return array;
    }
    else if (j.is_object()) {
        JsonMap map;
        for (auto it = j.begin(); it != j.end(); ++it) {
            map[it.key()] = json_value_to_any(it.value());
        }
        return map;
    }
    
    throw std::runtime_error("Unknown JSON type");
}

nlohmann::json to_json(const JsonMap& map) {
    nlohmann::json result = nlohmann::json::object();
    
    for (const auto& [key, value] : map) {
        result[key] = any_to_json_value(value);
    }
    
    return result;
}

nlohmann::json any_to_json_value(const std::any& value) {
    try {
        if (!value.has_value()) {
            return nullptr;
        }
        
        if (value.type() == typeid(std::nullptr_t)) {
            return nullptr;
        }
        else if (value.type() == typeid(bool)) {
            return std::any_cast<bool>(value);
        }
        else if (value.type() == typeid(int)) {
            return std::any_cast<int>(value);
        }
        else if (value.type() == typeid(int64_t)) {
            return std::any_cast<int64_t>(value);
        }
        else if (value.type() == typeid(double)) {
            return std::any_cast<double>(value);
        }
        else if (value.type() == typeid(float)) {
            return std::any_cast<float>(value);
        }
        else if (value.type() == typeid(std::string)) {
            return std::any_cast<std::string>(value);
        }
        else if (value.type() == typeid(const char*)) {
            return std::string(std::any_cast<const char*>(value));
        }
        else if (value.type() == typeid(JsonArray)) {
            const auto& array = std::any_cast<const JsonArray&>(value);
            nlohmann::json json_array = nlohmann::json::array();
            
            for (const auto& element : array) {
                json_array.push_back(any_to_json_value(element));
            }
            
            return json_array;
        }
        // Handle objects/maps
        else if (value.type() == typeid(JsonMap)) {
            const auto& map = std::any_cast<const JsonMap&>(value);
            nlohmann::json json_obj = nlohmann::json::object();
            
            for (const auto& [key, val] : map) {
                json_obj[key] = any_to_json_value(val);
            }
            
            return json_obj;
        }
    }
    catch (const std::bad_any_cast& e) {
        std::cerr << "Type conversion error: " << e.what() << std::endl;
    }
    
    return nullptr;
}
