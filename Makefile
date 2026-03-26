SHELL:=/bin/bash
MAKEFLAGS += --no-print-directory
.NOTPARALLEL:
ROOT_DIR:=$(shell dirname "$(realpath $(firstword $(MAKEFILE_LIST)))")

# This will automatically check if submodules have been updated when the 
# Makefile is invoked for the first time. 
MAKE_GADGETS_DIR := adore_cli/make_gadgets
MAKE_GADGETS_HAS_FILES := $(shell [ -d $(MAKE_GADGETS_DIR) ] && [ -n "$$(find $(MAKE_GADGETS_DIR) -mindepth 1 -maxdepth 1 -not -name '.git' 2>/dev/null)" ] && echo "yes")
ifeq ($(MAKE_GADGETS_HAS_FILES),)
    $(shell git submodule update --init --recursive >&2 || true)
endif

$(shell git config core.hooksPath .githooks >&2 || true)


include ${MAKE_GADGETS_DIR}/make_gadgets.mk

.EXPORT_ALL_VARIABLES:
SOURCE_DIRECTORY:=${ROOT_DIR}
SUBMODULES_PATH:=${ROOT_DIR}
VENDOR_PATH:=${ROOT_DIR}/vendor
ROS_NODE_PATH:=${ROOT_DIR}/ros2_workspace/src
ADORE_LIBRARY_PATH:=${ROOT_DIR}/libraries
DOCKER_BUILDKIT?=1
DOCKER_CONFIG?=


# Branch information
BRANCH:=$(shell bash ${MAKE_GADGETS_DIR}/tools/branch_name.sh)

include ${SUBMODULES_PATH}/adore_cli/ci_teststand/ci_teststand.mk
include utils.mk
include adore_cli/adore_cli.mk
include adore_cli/package.mk

$(shell [ -d "$(VENDOR_PATH)/build" ] || cd vendor && $(MAKE) --no-print-directory build >&2)

.PHONY: build
build: docker_host_context_check clean stop_adore_cli build_vendor_libraries build_adore_cli build_ros_workspace build_services ## Build and setup adore cli
	make clean_tag_history

.PHONY: build_adore_embedded
build_adore_embedded: docker_host_context_check # Build ADORe Embedded docker image
	cd adore_embedded && make build

.PHONY: build_all
build_all: clean build #build_services

.PHONY: build_services
build_services: ## Build ADORe supporting services such as Foxglove Studio aka Lichtblick Suite 
	cd tools/lichtblick && make build

.PHONY: start_services
start_services: docker_host_context_check ## Start ADORe supporting services  
	cd tools/lichtblick && make start

.PHONY: stop_services
stop_services: docker_host_context_check ## Stop ADORe supporting services 
	cd tools/lichtblick && make stop

.PHONY: build_vendor_libraries
build_vendor_libraries: docker_host_context_check ## Builds vendor libraries located in: ${VENDOR_PATH}
	cd "${VENDOR_PATH}" && make build

.PHONY: build_documentation
build_documentation: docker_host_context_check ## Builds ADORe Documentation in: ./documentation
	echo todo
	#cd documentation && make build

.PHONY: build_ros_workspace
build_ros_workspace:  ## Builds ROS2 workspace located in: ${ROS_NODE_PATH}
	if [ -f /.dockerenv ]; then \
		cd ros2_workspace && make build; \
	else \
		make run cmd="cd ros2_workspace && make build"; \
	fi

.PHONY: check_adore_binaries
check_adore_binaries: ## Checks for ADORe binaries
	bash tools/check_adore_binaries.sh

.PHONY: clean
clean: docker_host_context_check stop clean_adore_cli clean_tag_history ## Clean ADORe build artifacts 
	cd vendor && make clean
	cd ros2_workspace && make clean
	rm -rf build

.PHONY: lint_nodes
lint_nodes:
	@if [ -f /.dockerenv ]; then \
        clang-format -Werror -i -output-replacements-xml --checks=* -dry-run $(shell find ros2_workspace/src -type f \( -name "*.cpp" -or -name "*.hpp" -or -name "*.h" \)); \
    else \
        make run cmd="clang-format -Werror -i --checks=* -output-replacements-xml -dry-run $(shell find ros2_workspace/src -type f \( -name "*.cpp" -or -name "*.hpp" -or -name "*.h" \))"; \
    fi

.PHONY: due_diligence_scan
due_diligence_scan: ## Scan repo for eclipse due diligence, checks if source files have the proper doc header.
	python3 tools/eclipse_due_diligence_scanner.py --ignore tools/.eclipse_due_diligance_ignore 

.PHONY: due_diligence_fix
due_diligence_fix: ## Fix due diligence issues
	python3 tools/eclipse_due_diligence_scanner.py --ignore tools/.eclipse_due_diligance_ignore --fix

.PHONY: benchmark
benchmark: ## Run the ROS Topic benchmark script 
	if [ -f /.dockerenv ]; then \
		bash tools/ros_topic_benchmark.sh; \
	else \
		make run cmd="bash tools/ros_topic_benchmark.sh"; \
	fi

.PHONY: package_adore_ros2_msgs
package_adore_ros2_msgs: ## Build & package adore_ros2_msgs 
	if [ -f /.dockerenv ]; then \
		cd ros2_workspace && make package_adore_ros2_msgs; \
	else \
		make run cmd="cd ros2_workspace && make package_adore_ros2_msgs"; \
	fi

.PHONY: test
test: ## Run ADORe Unit Tests
	bash .ci test

