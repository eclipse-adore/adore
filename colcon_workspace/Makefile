SHELL := /bin/zsh
.DEFAULT_GOAL := help

ROOT_DIR := $(shell dirname "$(realpath $(firstword $(MAKEFILE_LIST)))")
ROS_DISTRO := $(shell echo "$(ROS_DISTRO)")
NPROC := $(shell nproc)

# === Helper Macros ===
define source_ros
source /opt/ros/$(ROS_DISTRO)/setup.zsh; \
[ -f install/local_setup.zsh ] && source install/local_setup.zsh || true
endef

COLCON_CMD = colcon build \
	--parallel-workers $(NPROC) \
	--symlink-install \
	--continue-on-error \
	--cmake-args -DCMAKE_POSITION_INDEPENDENT_CODE=ON -DCMAKE_BUILD_TYPE=Release

# === Targets ===

.PHONY: build
build: ## Build all packages in adore_scenarios selectively
	$(call source_ros) && \
	$(COLCON_CMD) --packages-select $(shell colcon list --base-paths src adore_scenarios --names-only)

.PHONY: clean
clean: ## Remove build/install/log artifacts
	rm -rf build/ install/ log/

.PHONY: clean_build
clean_build: clean build ## Clean and then build

.PHONY: test
test: ## Run all tests, excluding vendor packages
	$(call source_ros) && \
	colcon test \
		--event-handlers console_cohesion+ \
		--packages-skip $(shell colcon list --base-paths src/vendor --names-only); \
	colcon test-result --verbose

.PHONY: force_kill_ros2
force_kill_ros2: ## Forcefully kill any lingering ROS 2 or colcon processes
	@echo "Forcefully killing lingering ROS 2 processes..."
	-pkill -9 -f ros2 || echo "No ros2 nodes running."
	-pkill -9 -f rclpy || echo "No rclpy nodes running."
	-pkill -9 -f launch || echo "No launch processes running."
	-pkill -9 -f colcon || echo "No colcon processes running."
	@echo "Done."

.PHONY: help
help: ## Show this help message
	@grep -E '^[a-zA-Z0-9_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'


.PHONY: build_scenarios
build_scenarios: ## Build vendor packages in adore_scenarios selectively
	$(call source_ros) && \
	$(COLCON_CMD) --packages-select $(shell colcon list --base-paths adore_sceanrios --names-only)

.PHONY: build_conversions
build_conversions: ## Build library packages in adore_conversions selectively
	$(call source_ros) && \
	$(COLCON_CMD) --packages-select $(shell colcon list --base-paths src/conversions --names-only)

.PHONY: build_libraries
build_libraries: ## Build library packages in libraries selectively
	$(call source_ros) && \
	$(COLCON_CMD) --packages-select $(shell colcon list --base-paths src/libraries --names-only)

.PHONY: build_nodes
build_nodes: ## Build library packages in nodes selectively
	$(call source_ros) && \
	$(COLCON_CMD) --packages-select $(shell colcon list --base-paths src/nodes --names-only)

.PHONY: build_messages
build_messages: ## Build library packages in ros2_messages selectively
	$(call source_ros) && \
	$(COLCON_CMD) --packages-select $(shell colcon list --base-paths src/ros2_messages --names-only)

.PHONY: build_vendor
build_vendor: ## Build vendor packages in vendor selectively
	$(call source_ros) && \
	$(COLCON_CMD) --packages-select $(shell colcon list --base-paths src/vendor --names-only)
