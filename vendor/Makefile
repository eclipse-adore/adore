SHELL:=/bin/bash

.DEFAULT_GOAL := all

ROOT_DIR:=$(shell dirname "$(realpath $(firstword $(MAKEFILE_LIST)))")
SUBMODULES_PATH:=${ROOT_DIR}

MAKEFLAGS += --no-print-directory

.PHONY:build
build:  ## build all vendor libraries and copy output to ./build
	cd mathematics_toolbox && make build
	cd OptiNLC && make build
	cd ros2_observer && make build
	cd libOpenDRIVE && make build
	cd helix && make build
	mkdir -p build
	cp mathematics_toolbox/eigen/build build/eigen -r
	cp mathematics_toolbox/osqp/build build/osqp -r
	cp OptiNLC/OptiNLC/build build/OptiNLC -r
	cp ros2_observer/build build/ros2_observer -r
	cp libOpenDRIVE/libOpenDRIVE/build build/libOpenDRIVE -r
	cp helix/build build/helix -r

#	cd build/eigen && find . -type f -exec sed -i "s|/tmp/|$$(pwd)/|g" {} +
#	cd build/osqp && find . -type f -exec sed -i "s|/tmp/|$$(pwd)/|g" {} +

.PHONY: install
install:
	@if [ ! -d "build" ]; then \
        echo "ERROR: The vendor build directory: ${ROOT_DIR}/build does not exist. Did you build the vendor libraries with 'make build'?"; \
        exit 1; \
    fi
	find build -maxdepth 2 -type f -name "*.deb" -print0 | xargs -0 sudo dpkg -i --force-all 

.PHONY: clean
clean: 
	rm -rf build
	cd OptiNLC && make clean
	cd mathematics_toolbox && make clean
	cd ros2_observer && make clean
	cd libOpenDRIVE && make clean
	cd helix && make clean
