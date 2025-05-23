SHELL:=/bin/bash

.DEFAULT_GOAL := build

ROOT_DIR:=$(shell dirname "$(realpath $(firstword $(MAKEFILE_LIST)))")

.PHONY: help
help:
	@printf "Usage: make \033[36m<target>\033[0m\n%s\n" "$$(awk 'BEGIN {FS = ":.*##"} /^[a-zA-Z0-9_-]+:.*?##/ { printf "  \033[36m%-10s\033[0m %s\n", $$1, $$2 } /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) }' $(MAKEFILE_LIST) | sort | uniq)"


#.PHONY: build
#build:
#	mkdir -p build
#	cd build && cmake .. -D BUILD_EXECUTABLES=ON && make 

.PHONY: build
build: ## Build ADORe libraries. Must be built in the ADORe CLI Docker context!
	rm -rf build
	mkdir -p build
	#cd build && cmake .. -D BUILD_LIBRARIES=ON && make
	cd build && cmake .. && make
	cd build && cmake .. && make -j $(nproc) && cd .. && mv build/CMakeCache.txt build/CMakeCache.txt.libraries
#	cd build && mv CMakeCache.txt CMakeCache.txt.libraries

.PHONY: clean
clean:
	rm -rf ${ROOT_DIR}/build

.PHONY: print_cmake_target_info
print_cmake_target_info: ## Prints a summary of all defined CMake targets and exits.  
	mkdir -p build
	cd build && cmake .. -D PRINT_TARGET_INFO=ON 

.PHONY: print_cmake_package_info
print_cmake_package_info: ## Prints a summary list of all defined CMake packages and exits.
	mkdir -p build
	cd build && cmake .. -D PRINT_PACKAGE_INFO=ON 

.PHONY: print_cmake_library_info
print_cmake_library_info:
	mkdir -p build
	cd build && cmake .. -D PRINT_LIBRARY_INFO=ON 

.PHONY: print_cmake_variables
print_cmake_variables:
	mkdir -p build
	cd build && cmake .. -D PRINT_CMAKE_VARIABLES=ON 
