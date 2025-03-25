#include <nlohmann/json.hpp>
#include <string>
#include <fstream>
#include <iostream>

void JsonFileExampleLoader(std::string fileName){
    std::ifstream f(fileName);
    if(f.fail())
    {
        std::cout << "Failed to load Json" << std::endl;
        return;
    }

    nlohmann::json jsonFile = nlohmann::json::parse(f);

    std::cout << jsonFile.dump() << std::endl;
}

int main(){
    JsonFileExampleLoader("checkme.json");
    return 0;
}
