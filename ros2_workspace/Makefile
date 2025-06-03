SHELL:=/bin/bash

.DEFAULT_GOAL := help 

ROOT_DIR:=$(shell dirname "$(realpath $(firstword $(MAKEFILE_LIST)))")

.PHONY: help
help:
	@printf "Usage: make \033[36m<target>\033[0m\n%s\n" "$$(awk 'BEGIN {FS = ":.*##"} /^[a-zA-Z0-9_-]+:.*?##/ { printf "  \033[36m%-10s\033[0m %s\n", $$1, $$2 } /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) } ' $(MAKEFILE_LIST) | sort | uniq)"

.PHONY: build
build: ## Build all ROS2 packages
	source /opt/ros/$${ROS_DISTRO}/setup.bash && colcon build --parallel-workers $$(nproc) && source install/local_setup.sh

.PHONY: build_release
build_release: ## Build all ROS2 packages
	source /opt/ros/$${ROS_DISTRO}/setup.bash && colcon build --parallel-workers $$(nproc) --cmake-args -DCMAKE_BUILD_TYPE=Release && source install/local_setup.sh

.PHONY: build_user_libraries
build_user_libraries: 
	cd ../libraries && make build && cd ../ros2_workspace

.PHONY: build_libraries_and_nodes
build_libraries_and_nodes: build_user_libraries build_release


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

.PHONY: launch
launch: ## Launch a ROS2 scenario
	@base_dir="../adore_scenarios"; \
	export PYTHONPATH="$$PYTHONPATH:$$base_dir"; \
	selected_file=$$(find $$base_dir -type f -name "*.py" | grep -v "/integration_tests/" | sed 's|^\.\./adore_scenarios/||' | fzf --prompt="Select a scenario to launch: "); \
	if [ -n "$$selected_file" ]; then \
		echo "Launching $$selected_file..."; \
		ros2 launch "$$base_dir/$$selected_file"; \
	else \
		echo "No file selected."; \
	fi

.PHONY: integration_tests
integration_tests: ## Run pytest inside adore_scenarios
	@base_dir="../adore_scenarios"; \
	PYTHONPATH="$$PYTHONPATH:$$base_dir" pytest "$$base_dir"


.PHONY: force_kill_ros2
force_kill_ros2: ## Forcefully kill all ROS 2 processes
	@echo "Forcefully killing all lingering ROS 2 nodes..."
	@pkill -9 -f ros2 || echo "No ROS 2 nodes found."
	@pkill -9 -f rclpy || echo "No Python-based ROS 2 nodes found."
	@pkill -9 -f launch || echo "No ROS 2 launch processes found."
	@pkill -9 -f colcon || echo "No lingering colcon processes found."
	@echo "All done!"
