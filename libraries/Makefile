SHELL:=/bin/bash

.DEFAULT_GOAL := build

ROOT_DIR:=$(shell dirname "$(realpath $(firstword $(MAKEFILE_LIST)))")
RAM_KB := $(shell grep MemTotal /proc/meminfo | awk '{print $$2}')
RAM_GB := $(shell echo $$(( $(RAM_KB) / 1024 / 1024 )))

.PHONY: help
help:
	@printf "Usage: make \033[36m<target>\033[0m\n%s\n" "$$(awk 'BEGIN {FS = ":.*##"} /^[a-zA-Z0-9_-]+:.*?##/ { printf "  \033[36m%-10s\033[0m %s\n", $$1, $$2 } /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) }' $(MAKEFILE_LIST) | sort | uniq)"

.PHONY: check_resources
check_resources:
	@echo "Detected RAM: $(RAM_KB) kB ($(RAM_GB) GB)"
	@JOBS=$$(if [ "$(RAM_KB)" -ge 8000000 ]; then echo $$(nproc); else echo 1; fi); \
	echo "Using $$JOBS job(s) for build..."; \
	true

.PHONY: build
build: build_release ## Build ADORe libraries (default)
	@echo "✅ Libraries build complete"
	@touch build/build.success

.PHONY: build_release
build_release: check_resources ## Build ADORe libraries in Release mode
	@JOBS=$$(if [ "$(RAM_KB)" -ge 8000000 ]; then echo $$(nproc); else echo 1; fi); \
	rm -rf build; \
	mkdir -p build; \
	cd build && cmake -DCMAKE_BUILD_TYPE=Release .. \
		&& make -j $$JOBS \
		&& mv CMakeCache.txt CMakeCache.txt.libraries
	@echo "✅ Libraries release build complete"
	@touch build/build_release.success

.PHONY: build_debug
build_debug: check_resources ## Build ADORe libraries in Debug mode
	@JOBS=$$(if [ "$(RAM_KB)" -ge 8000000 ]; then echo $$(nproc); else echo 1; fi); \
	rm -rf build; \
	mkdir -p build; \
	cd build && cmake -DCMAKE_BUILD_TYPE=Debug .. \
		&& make -j $$JOBS \
		&& mv CMakeCache.txt CMakeCache.txt.libraries
	@echo "✅ Libraries debug build complete"
	@touch build/build_debug.success

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
