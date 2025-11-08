SHELL := /bin/zsh
.DEFAULT_GOAL := build

.PHONY: \
	build build_image \
	clean clean_cli \
	cli stop_cli \
	save load \
	gui edit_roads lichtblick \
	test docs ci

WORKSPACE_ROOT := $(PWD)
ROS_DISTRO := jazzy

# ----------------------------------------------------------------------
# Docker-backed targets (dev image)
# ----------------------------------------------------------------------

build_image:
	@WORKSPACE_ROOT="$(WORKSPACE_ROOT)" ROS_DISTRO="$(ROS_DISTRO)" \
		.docker/scripts/build_image.sh

# One-shot dev container (same behaviour as your original `build` target:
# ensures image exists, then runs a container in colcon_workspace)
build:
	@WORKSPACE_ROOT="$(WORKSPACE_ROOT)" ROS_DISTRO="$(ROS_DISTRO)" \
		.docker/scripts/run_build.sh

clean_cli:
	@WORKSPACE_ROOT="$(WORKSPACE_ROOT)" ROS_DISTRO="$(ROS_DISTRO)" \
		.docker/scripts/clean_images.sh

clean: clean_cli
	@echo "--- Cleaning local colcon build artifacts ---"
	rm -rf "$(WORKSPACE_ROOT)/build" "$(WORKSPACE_ROOT)/install" "$(WORKSPACE_ROOT)/log"

cli:
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

test:
	@WORKSPACE_ROOT="$(WORKSPACE_ROOT)" ROS_DISTRO="$(ROS_DISTRO)" \
		.docker/scripts/run_tests.sh

docs:
	@WORKSPACE_ROOT="$(WORKSPACE_ROOT)" ROS_DISTRO="$(ROS_DISTRO)" \
		.docker/scripts/run_docs.sh

# Convenience: full CI locally
ci: test docs
