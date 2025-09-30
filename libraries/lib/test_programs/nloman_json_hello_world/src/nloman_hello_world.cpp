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
