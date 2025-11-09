SHELL := /bin/zsh
.DEFAULT_GOAL := build

.PHONY: \
	build build_image \
	clean clean_cli \
	cli stop_cli \
	save load \
	gui edit_roads lichtblick \
	test docs ci \
	setup_colcon_src

WORKSPACE_ROOT := $(PWD)
ROS_DISTRO := jazzy

SETUP_COLCON_SCRIPT := .docker/scripts/setup_colcon_src.sh

# ----------------------------------------------------------------------
# Symlink setup for colcon workspace
# ----------------------------------------------------------------------

setup_colcon_src:
	@if [ -x "$(SETUP_COLCON_SCRIPT)" ]; then \
		echo "--- Ensuring colcon_workspace/src symlinks are set up ---"; \
		"$(SETUP_COLCON_SCRIPT)"; \
	else \
		echo "ERROR: $(SETUP_COLCON_SCRIPT) not found or not executable" >&2; \
		exit 1; \
	fi

# ----------------------------------------------------------------------
# Docker-backed targets (dev image)
# ----------------------------------------------------------------------

build_image:
	@WORKSPACE_ROOT="$(WORKSPACE_ROOT)" ROS_DISTRO="$(ROS_DISTRO)" \
		.docker/scripts/build_image.sh

# Ensure symlinks exist before running the build inside Docker
build: setup_colcon_src
	@WORKSPACE_ROOT="$(WORKSPACE_ROOT)" ROS_DISTRO="$(ROS_DISTRO)" \
		.docker/scripts/run_build.sh

clean_cli:
	@WORKSPACE_ROOT="$(WORKSPACE_ROOT)" ROS_DISTRO="$(ROS_DISTRO)" \
		.docker/scripts/clean_images.sh

clean: clean_cli
	@echo "--- Cleaning local colcon build artifacts ---"
	rm -rf "$(WORKSPACE_ROOT)/build" "$(WORKSPACE_ROOT)/install" "$(WORKSPACE_ROOT)/log"

# Ensure symlinks also exist when dropping into the dev container
cli: setup_colcon_src
	@WORKSPACE_ROOT="$(WORKSPACE_ROOT)" ROS_DISTRO="$(ROS_DISTRO)" \
		.docker/scripts/cli.sh

stop_cli:
	@WORKSPACE_ROOT="$(WORKSPACE_ROOT)" ROS_DISTRO="$(ROS_DISTRO)" \
		.docker/scripts/stop_cli.sh

save:
	@WORKSPACE_ROOT="$(WORKSPACE_ROOT)" ROS_DISTRO="$(ROS_DISTRO)" \
		.docker/scripts/save_image.sh

load:
	@WORKSPACE_ROOT="$(WORKSPACE_ROOT)" ROS_DISTRO="$(ROS_DISTRO)" \
		.docker/scripts/load_image.sh

# ----------------------------------------------------------------------
# Local tools (unchanged)
# ----------------------------------------------------------------------

gui:
	python3 tools/adore_gui.py

edit_roads:
	python3 tools/edit_roads.py

lichtblick:
	./tools/run_lichtblick.sh

# ----------------------------------------------------------------------
# CI helpers (use the CI image under the hood)
# ----------------------------------------------------------------------

# Tests expect a valid colcon workspace layout
test: setup_colcon_src
	@WORKSPACE_ROOT="$(WORKSPACE_ROOT)" ROS_DISTRO="$(ROS_DISTRO)" \
		.docker/scripts/run_tests.sh

# Docs pipeline may also rely on the workspace layout
docs: setup_colcon_src
	@WORKSPACE_ROOT="$(WORKSPACE_ROOT)" ROS_DISTRO="$(ROS_DISTRO)" \
		.docker/scripts/run_docs.sh

# Convenience: full CI locally
ci: test docs
