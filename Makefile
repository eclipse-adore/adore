SHELL:=/bin/bash

ROOT_DIR:=$(shell dirname "$(realpath $(firstword $(MAKEFILE_LIST)))")

MAKE_GADGETS_DIR:=tools/adore_cli/make_gadgets

MAKE_GADGETS_FILES := $(wildcard $(MAKE_GADGETS_DIR)/*)
ifeq ($(MAKE_GADGETS_FILES),)
    $(shell git submodule update --init --recursive)
endif


include ${MAKE_GADGETS_DIR}/make_gadgets.mk
#include tools/make_gadgets/docker/docker-tools.mk

.EXPORT_ALL_VARIABLES:
SOURCE_DIRECTORY:=${ROOT_DIR}
ADORE_CLI_WORKING_DIRECTORY:=${ROOT_DIR}
ADORE_DIRECTORY:=${ROOT_DIR}
SUBMODULES_PATH:=${ROOT_DIR}/tools
VENDOR_PATH:=${ROOT_DIR}/vendor
ROS_NODE_PATH:=${ROOT_DIR}/ros2_workspace/src
ADORE_LIBRARY_PATH:=${ROOT_DIR}/libraries
#BRANCH:=$(shell make get_sanitized_branch_name)
PARENT_BRANCH:= $(shell cd "${ROOT_DIR}" && bash $(MAKE_GADGETS_DIR)/tools/branch_name.sh 2>/dev/null || echo NOBRANCH)
PARENT_SHORT_HASH:=$(shell cd "${ROOT_DIR}" && git rev-parse --short HEAD 2>/dev/null || echo NOHASH)
BRANCH:=$(shell bash ${MAKE_GADGETS_DIR}/tools/branch_name.sh)
ADORE_CLI_BRANCH:=$(shell bash ${MAKE_GADGETS_DIR}/tools/branch_name.sh)
ADORE_CLI_IMAGE:=$(shell cd tools/adore_cli && make image_adore_cli)_${BRANCH}
ADORE_CLI_CONTAINER_NAME:=$(subst :,_,${ADORE_CLI_IMAGE})
ROS_HOME:="${ROOT_DIR}/.log/.ros"
TRACE_DURATION_s:=5


include ${SUBMODULES_PATH}/adore_cli/ci_teststand/ci_teststand.mk
include utils.mk
include ${SUBMODULES_PATH}/adore_cli/adore_cli.mk

.PHONY: build
build: clean stop_adore_cli build_vendor_libraries build_adore_cli_core build_adore_cli build_user_libraries build_ros_nodes ## Build and setup adore cli

.PHONY: build_all
build_all: clean build build_services

.PHONY: build_services
build_services: ## Build ADORe supporting services such as Foxglove Studio aka Lichtblick Suite 
	cd tools/lichtblick && make build

.PHONY: start_services
start_services: ## Start ADORe supporting services  
	cd tools/lichtblick && make start

.PHONY: stop_services
stop_services: ## Stop ADORe supporting services 
	cd tools/lichtblick && make stop

.PHONY: build_vendor_libraries
build_vendor_libraries: ## Builds vendor libraries located in: ${VENDOR_PATH}
	cd "${VENDOR_PATH}" && make build

.PHONY: build_user_libraries
build_user_libraries: ## Builds user libraries located in: ${ADORE_LIBRARY_PATH}
	make run cmd="cd libraries && make build"

.PHONY: build_documentation
build_documentation: ## Builds ADORe Documentation in: ./documentation
	cd documentation && make build

.PHONY: build_ros_nodes
build_ros_nodes: ## Builds ROS2 nodes located in: ${ROS_NODE_PATH}
	make run cmd="cd ros2_workspace && make build"

.PHONY: clean
clean: clean_adore_cli ## Clean ADORe  build artifacts 
	cd vendor && make clean
	cd libraries && make clean
	cd ros2_workspace && make clean
	rm -rf build

.PHONY: trace
trace: ## Generate tracing data with ros2_traceing 
	make adore_cli_run cmd="ros2-tracer -t ${TRACE_DURATION_s} -o"
	cd vendor/ros2_observer/trace_compass && make start

.PHONY:lint_nodes
lint_nodes:
	@if [ -f /.dockerenv ]; then \
        clang-format -Werror -i -output-replacements-xml --checks=* -dry-run $(shell find ros2_workspace/src -type f \( -name "*.cpp" -or -name "*.hpp" -or -name "*.h" \)); \
    else \
        make run cmd="clang-format -Werror -i --checks=* -output-replacements-xml -dry-run $(shell find ros2_workspace/src -type f \( -name "*.cpp" -or -name "*.hpp" -or -name "*.h" \))"; \
    fi

.PHONY: test
test: ci_test



