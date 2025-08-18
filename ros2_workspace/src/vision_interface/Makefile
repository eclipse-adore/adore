SHELL:=/bin/bash

.PHONY: help
help:
	@printf "Usage: make \033[36m<target>\033[0m\n%s\n" "$$(awk 'BEGIN {FS = ":.*##"} /^[a-zA-Z0-9_-]+:.*?##/ { printf "  \033[36m%-10s\033[0m %s\n", $$1, $$2 } /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) }' $(MAKEFILE_LIST) | sort | uniq)"



SCRIPT_DIRECTORY := $(shell dirname $(realpath $(lastword $(MAKEFILE_LIST))))
ROS2_WORKSPACE := $(shell \
    current_dir=$(SCRIPT_DIRECTORY); \
    while [ "$$current_dir" != "/" ]; do \
        if [ -d "$$current_dir/build" ] && \
           [ -d "$$current_dir/install" ] && \
           [ -d "$$current_dir/log" ] && \
           [ -d "$$current_dir/src" ]; then \
            echo "$$current_dir"; \
            exit 0; \
        fi; \
        current_dir=$$(dirname "$$current_dir"); \
    done; \
    echo "Error: ROS 2 workspace not found." >&2; \
    exit 1; \
)

ROS2_PACKAGE := $(shell grep -oP '<name>\K[^<]*' $(SCRIPT_DIRECTORY)/package.xml | tr -d '[:space:]')
DEPENDENCIES := $(shell grep -oP '<depend>\K[^<]*' $(SCRIPT_DIRECTORY)/package.xml | tr '\n' ' ' | tr -s ' ' | sed 's/ $$//')


.PHONY: build
build: build_dependencies ##         Build ROS2 Node. Same as running `colcon build --packages-select <package name>`
	@echo "Building: ${ROS2_PACKAGE}"
	@echo "  Using ROS 2 workspace: ${ROS2_WORKSPACE}"
	cd $(ROS2_WORKSPACE) && colcon build --packages-select ${ROS2_PACKAGE}

.PHONY: build_dependencies
build_dependencies: ## Build all node dependencies
	@echo "Building dependencies..."
	@echo "  Using ROS 2 workspace: ${ROS2_WORKSPACE}"
	@cd $(ROS2_WORKSPACE) && for dependency in $(DEPENDENCIES); do \
	    cd $(ROS2_WORKSPACE) && colcon build --packages-select $$dependency; \
	done

.PHONY: test
test: build ##         Execute unit tests
	@echo "Running tests..."
	@source $(ROS2_WORKSPACE)/install/setup.bash && \
    if [ -z "$$(ros2 pkg list | grep $(ROS2_PACKAGE))" ]; then \
        echo "ERROR: ROS2 Package: '$(ROS2_PACKAGE)' not found. Did you build it?" >&2; \
        exit 1; \
    fi && \
    cd $(ROS2_WORKSPACE) && colcon test --packages-select ${ROS2_PACKAGE} --event-handlers console_direct+

.PHONY: run
run: ##         Run the node
	@echo "Running ROS 2 node: ${ROS2_PACKAGE}..."
	@echo "  Using ROS 2 workspace: ${ROS2_WORKSPACE}"
	@source $(ROS2_WORKSPACE)/install/setup.bash && \
    if [ -z "$$(ros2 pkg list | grep $(ROS2_PACKAGE))" ]; then \
        echo "ERROR: ROS2 Package: '$(ROS2_PACKAGE)' not found. Did you build it?" >&2; \
        exit 1; \
    fi && \
    cd $(ROS2_WORKSPACE) && ros2 run $(ROS2_PACKAGE) $(ROS2_PACKAGE)

.PHONY: clean
clean: ##         Clean build artifacts
	rm -rf $(ROS2_WORKSPACE)/build/$(ROS2_PACKAGE) $(ROS2_WORKSPACE)/install/$(ROS2_PACKAGE)

