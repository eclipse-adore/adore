#include "adore_util/json.h"
#include <iostream>
#include <cassert>
#include <fstream>

// Constant example JSON string
const char* EXAMPLE_JSON = R"({
  "person": {
    "name": "John Doe",
    "age": 30,
    "isEmployed": true,
    "address": {
      "street": "123 Main St",
      "city": "Anytown",
      "zipcode": 12345
    },
    "phones": [
      {
        "type": "home",
        "number": "555-1234"
      },
      {
        "type": "work",
        "number": "555-5678"
      }
    ],
    "skills": ["programming", "design", "communication"],
    "spouse": null,
    "salary": 75000.50
  }
})";

int main() {
    try {
        std::cout << "JSON Parser and Serializer Test using nlohmann/json\n";
        std::cout << "================================================\n\n";
        
        // PART 1: Parse the constant JSON string
        std::cout << "=== PART 1: Parse Example JSON String ===\n";
        std::cout << "Original JSON:\n" << EXAMPLE_JSON << "\n\n";
        
        // Parse the JSON string
        nlohmann::json parsed_json = nlohmann::json::parse(EXAMPLE_JSON);
        JsonMap root_map = from_json(parsed_json);
        
        // Access the person object
        JsonMap person = std::any_cast<JsonMap>(root_map["person"]);
        
        // Display basic properties
        std::string name = std::any_cast<std::string>(person["name"]);
        int64_t age = std::any_cast<int64_t>(person["age"]);
        bool isEmployed = std::any_cast<bool>(person["isEmployed"]);
        double salary = std::any_cast<double>(person["salary"]);
        
        std::cout << "Basic properties:\n";
        std::cout << "  Name: " << name << "\n";
        std::cout << "  Age: " << age << "\n";
        std::cout << "  Employed: " << (isEmployed ? "Yes" : "No") << "\n";
        std::cout << "  Salary: " << salary << "\n\n";
        
        // Access nested object
        JsonMap address = std::any_cast<JsonMap>(person["address"]);
        std::cout << "Address:\n";
        std::cout << "  Street: " << std::any_cast<std::string>(address["street"]) << "\n";
        std::cout << "  City: " << std::any_cast<std::string>(address["city"]) << "\n";
        std::cout << "  Zipcode: " << std::any_cast<int64_t>(address["zipcode"]) << "\n\n";
        
        // Access array of objects
        JsonArray phones = std::any_cast<JsonArray>(person["phones"]);
        std::cout << "Phone numbers:\n";
        for (size_t i = 0; i < phones.size(); i++) {
            JsonMap phone = std::any_cast<JsonMap>(phones[i]);
            std::cout << "  " << std::any_cast<std::string>(phone["type"]) << ": " 
                      << std::any_cast<std::string>(phone["number"]) << "\n";
        }
        std::cout << "\n";
        
        // Access array of primitives
        JsonArray skills = std::any_cast<JsonArray>(person["skills"]);
        std::cout << "Skills:\n";
        for (size_t i = 0; i < skills.size(); i++) {
            std::cout << "  " << std::any_cast<std::string>(skills[i]) << "\n";
        }
        std::cout << "\n";
        
        // PART 2: Modify and re-serialize
        std::cout << "=== PART 2: Modify and Re-serialize ===\n";
        
        // Modify some values
        person["age"] = int64_t(31);  // Birthday!
        person["salary"] = 80000.00;  // Got a raise!
        
        // Add a new skill
        JsonArray& skills_ref = std::any_cast<JsonArray&>(person["skills"]);
        skills_ref.push_back(std::string("leadership"));
        
        // Add a new phone
        JsonMap mobile_phone;
        mobile_phone["type"] = std::string("mobile");
        mobile_phone["number"] = std::string("555-9876");
        JsonArray& phones_ref = std::any_cast<JsonArray&>(person["phones"]);
        phones_ref.push_back(mobile_phone);
        
        // Add a new property
        person["department"] = std::string("Engineering");
        
        // Update the root map
        root_map["person"] = person;
        
        // Convert back to JSON
        nlohmann::json modified_json = to_json(root_map);
        std::string modified_str = modified_json.dump(2);
        
        std::cout << "Modified JSON:\n" << modified_str << "\n\n";
        
        // Save to file
        std::ofstream out_file("modified_person.json");
        out_file << modified_str;
        out_file.close();
        std::cout << "Saved to modified_person.json\n\n";
        
        // PART 3: Round-trip test
        std::cout << "=== PART 3: Round-trip Test ===\n";
        
        // Parse the modified JSON back
        JsonMap reparsed_map = from_json(modified_json);
        JsonMap reparsed_person = std::any_cast<JsonMap>(reparsed_map["person"]);
        
        // Verify some changes
        std::cout << "Verifying changes:\n";
        std::cout << "  New age: " << std::any_cast<int64_t>(reparsed_person["age"]) << "\n";
        std::cout << "  New salary: " << std::any_cast<double>(reparsed_person["salary"]) << "\n";
        std::cout << "  New department: " << std::any_cast<std::string>(reparsed_person["department"]) << "\n";
        
        // Verify new phone
        JsonArray reparsed_phones = std::any_cast<JsonArray>(reparsed_person["phones"]);
        JsonMap last_phone = std::any_cast<JsonMap>(reparsed_phones[reparsed_phones.size()-1]);
        std::cout << "  New phone: " << std::any_cast<std::string>(last_phone["type"]) << " - " 
                  << std::any_cast<std::string>(last_phone["number"]) << "\n";
        
        // Verify new skill
        JsonArray reparsed_skills = std::any_cast<JsonArray>(reparsed_person["skills"]);
        std::cout << "  New skill: " << std::any_cast<std::string>(reparsed_skills[reparsed_skills.size()-1]) << "\n";
        
        std::cout << "\nAll tests completed successfully!\n";
        return 0;
    }
    catch (const std::exception& e) {
        std::cerr << "Error: " << e.what() << std::endl;
        return 1;
    }
}
