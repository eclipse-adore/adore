SHELL:=/bin/bash

.DEFAULT_GOAL := help 

ROOT_DIR:=$(shell dirname "$(realpath $(firstword $(MAKEFILE_LIST)))")

.PHONY: help
help:
	@printf "Usage: make \033[36m<target>\033[0m\n%s\n" "$$(awk 'BEGIN {FS = ":.*##"} /^[a-zA-Z0-9_-]+:.*?##/ { printf "  \033[36m%-10s\033[0m %s\n", $$1, $$2 } /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) } ' $(MAKEFILE_LIST) | sort | uniq)"

.PHONY: build
build: ## Build all ROS2 packages
	source /opt/ros/$${ROS_DISTRO}/setup.bash && colcon build --cmake-args -DCMAKE_BUILD_TYPE=Debug --parallel-workers $$(nproc)
	#source /opt/ros/$${ROS_DISTRO}/setup.bash && colcon build --continue-on-error --cmake-args -DCMAKE_BUILD_TYPE=Debug --parallel-workers $$(nproc)

.PHONY: build_continue_on_error
build_continue_on_error: ## Build all ROS2 packages, continue on error
	source /opt/ros/$${ROS_DISTRO}/setup.bash && colcon build --continue-on-error --cmake-args -DCMAKE_BUILD_TYPE=Debug --parallel-workers $$(nproc)

.PHONY: clean_build
clean_build: clean build ## Clean and build all ROS2 packages

.PHONY: clean
clean: ## Clean the ROS2 workspace
	rm -rf build/*
	rm -rf log/*
	rm -rf install/*

.PHONY: test
test:
	colcon test --pytest-args "-m 'not linter'" --event-handlers console_direct+

.PHONY: ccache_stats
ccache_stats: ## Print out CCache Stats 
	ccache -s -v
