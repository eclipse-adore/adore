SHELL:=/bin/bash

.DEFAULT_GOAL := all

ROOT_DIR:=$(shell dirname "$(realpath $(firstword $(MAKEFILE_LIST)))")
SUBMODULES_PATH:=${ROOT_DIR}

MAKEFLAGS += --no-print-directory

.PHONY:build
build:  ## build all vendor libraries and copy output to ./build
	cd ros2_observer && make build
	cd adore_model_checker && make build
	mkdir -p build
	cp ros2_observer/build build/ros2_observer -r
	cp adore_model_checker/build build/adore_model_checker -r


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
	cd adore_model_checker && make clean
	cd ros2_observer && make clean
