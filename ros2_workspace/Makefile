SHELL := /bin/bash
MAKEFLAGS += --no-print-directory

# --- Dependency Checks ---
.PHONY: check_ros2
check_ros2:
	@command -v ros2 >/dev/null 2>&1 || { \
		echo "ERROR: 'ros2' command not found. Call this inside the ADORe CLI docker context to avoid this error."; \
		exit 1; \
	}

.PHONY: check_colcon
check_colcon:
	@command -v colcon >/dev/null 2>&1 || { \
		echo "ERROR: 'colcon' command not found. Call this inside the ADORe CLI docker context to avoid this error."; \
		exit 1; \
	}

# A combined target for convenience
.PHONY: check_deps
check_deps: check_ros2 check_colcon


ROOT_DIR                 := $(shell dirname "$(realpath $(firstword $(MAKEFILE_LIST)))")
COLCON_DEFAULTS          := $(ROOT_DIR)/colcon_defaults.yaml
COLCON_DEFAULTS_TEMPLATE := $(ROOT_DIR)/colcon_defaults.yaml.template
RAM_KB                   := $(shell awk '/MemAvailable/{print $$2}' /proc/meminfo)
RAM_GB                   := $(shell awk '/MemAvailable/{print int($$2/1024/1024)}' /proc/meminfo)
PARALLEL_WORKERS := $(shell \
    mem_workers=$$(awk '/MemAvailable/{print int($$2/1024/1024/2)}' /proc/meminfo); \
    cpu_workers=$$(nproc); \
    echo $$(( mem_workers < cpu_workers ? mem_workers : cpu_workers )))

define patch_parallel_workers
	@sed -i 's/^\(\s*parallel-workers:\s*\).*/\1$(PARALLEL_WORKERS)/' $(COLCON_DEFAULTS)
endef

define ensure_colcon_defaults
	@if [ ! -f $(COLCON_DEFAULTS) ]; then \
		cp $(COLCON_DEFAULTS_TEMPLATE) $(COLCON_DEFAULTS); \
	fi
endef

.PHONY: help
help:
	@printf "Usage: make \033[36m<target>\033[0m\n%s\n" "$$(awk 'BEGIN {FS = ":.*##"} /^[a-zA-Z0-9_-]+:.*?##/ { printf "  \033[36m%-10s\033[0m %s\n", $$1, $$2 } /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) } ' $(MAKEFILE_LIST) | sort | uniq)"

.PHONY: build
build: check_deps ## Build all ROS2 packages
	$(call ensure_colcon_defaults)
	$(call patch_parallel_workers)
	@echo "Detected RAM: $(RAM_KB) kB ($(RAM_GB) GB)"
	@echo "Parallel workers: $(PARALLEL_WORKERS)"
	source /opt/ros/${ROS_DISTRO}/setup.bash && COLCON_DEFAULTS_FILE=$(COLCON_DEFAULTS) colcon build
	@echo "✅ ROS workspace build complete"
	touch build/build.success

.PHONY: build_release
build_release: check_deps ## Build all ROS2 packages in Release mode
	$(call ensure_colcon_defaults)
	$(call patch_parallel_workers)
	@echo "Detected RAM: $(RAM_KB) kB ($(RAM_GB) GB)"
	@echo "Parallel workers: $(PARALLEL_WORKERS)"
	source /opt/ros/${ROS_DISTRO}/setup.bash && COLCON_DEFAULTS_FILE=$(COLCON_DEFAULTS) colcon build && source install/local_setup.sh

.PHONY: build_single_core
build_single_core: check_deps ## Build all ROS2 packages, force single-threaded build regardless of RAM
	@echo "Executor mode: --executor sequential"
	source /opt/ros/${ROS_DISTRO}/setup.bash && colcon build --executor sequential

.PHONY: clean
clean: ## Clean the ROS2 workspace
	rm -rf build/*
	rm -rf log/*
	rm -rf install/*



.PHONY: clean_build
clean_build: clean build ## Clean and build all ROS2 packages

.PHONY: test
test: check_colcon ## Run ROS2 package tests
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

.PHONY: package
package: ## Package all ROS2 nodes as Debian packages
	bash tools/ros2_debian_packager.sh

.PHONY: package_adore_ros2_msgs
package_adore_ros2_msgs: ## Package adore_ros2_msgs as a Debian package
	bash tools/ros2_debian_packager.sh "adore_ros2_msgs"
	@echo "✅ adore_ros2_msgs packaging complete"
	touch build/adore_ros2_msgs.package.success

.PHONY: integration_tests
integration_tests: ## Run pytest inside adore_scenarios
	@base_dir="../adore_scenarios"; \
	PYTHONPATH="$$PYTHONPATH:$$base_dir" pytest "$$base_dir"

.PHONY: force_kill_ros2
force_kill_ros2: ## Forcefully kill all ROS 2 processes
	@echo "Forcefully killing all lingering ROS 2 nodes..."
	@pkill -9 -f ros2   || echo "No ROS 2 nodes found."
	@pkill -9 -f rclpy  || echo "No Python-based ROS 2 nodes found."
	@pkill -9 -f launch || echo "No ROS 2 launch processes found."
	@pkill -9 -f colcon || echo "No lingering colcon processes found."
	@echo "All done!!"
