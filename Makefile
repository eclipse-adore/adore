SHELL := /bin/zsh
.DEFAULT_GOAL := build

.PHONY: build clean cli gui edit_roads lichtblick build_image save load

WORKSPACE_ROOT := $(PWD)
ROS_DISTRO := jazzy

# Image + Container
DOCKER_IMAGE_BASE := adore_cli
DOCKER_CONTAINER_NAME := adore_cli

# Git + Arch Info
GIT_HASH := $(shell git rev-parse --short HEAD)
ARCH := $(shell uname -m)
IMAGE_TAG := $(GIT_HASH)-$(ARCH)

DOCKER_IMAGE_TAGGED := $(DOCKER_IMAGE_BASE):$(IMAGE_TAG)
DOCKER_IMAGE_LATEST := $(DOCKER_IMAGE_BASE):latest

# Optional: central ccache dir
LOCAL_CCACHE_DIR := $(WORKSPACE_ROOT)/.ccache

DOCKERFILE_MINIMAL := $(WORKSPACE_ROOT)/.docker/minimal/Dockerfile

build_image:
	docker build \
		-f $(DOCKERFILE_MINIMAL) \
		--build-arg USER_UID=$(shell id -u) \
		--build-arg USER_GID=$(shell id -g) \
		--build-arg USERNAME=$(USER) \
		-t $(DOCKER_IMAGE_LATEST) \
		-t $(DOCKER_IMAGE_TAGGED) \
		$(WORKSPACE_ROOT)

build: build_image
	docker run --rm -it --name $(DOCKER_CONTAINER_NAME) \
		-v "$(WORKSPACE_ROOT):/home/$(USER)/adore" \
		-w "/home/$(USER)/adore/colcon_workspace" \
		-e ROS_DISTRO=$(ROS_DISTRO) \
		$(DOCKER_IMAGE_LATEST) 

# --- Clean local artifacts and image ---
clean_cli:
	@echo "--- Removing Docker images $(DOCKER_IMAGE_LATEST) and $(DOCKER_IMAGE_TAGGED) if they exist ---"
	-docker rmi $(DOCKER_IMAGE_LATEST) || true
	-docker rmi $(DOCKER_IMAGE_TAGGED) || true

clean: clean_cli
	@echo "--- Cleaning local colcon build artifacts ---"
	rm -rf $(WORKSPACE_ROOT)/build $(WORKSPACE_ROOT)/install $(WORKSPACE_ROOT)/log

# --- Run interactive shell; re-use container if running ---
cli:
	@echo "--- Ensuring Docker image $(DOCKER_IMAGE_LATEST) is built ---"
	docker image inspect $(DOCKER_IMAGE_LATEST) >/dev/null 2>&1 || $(MAKE) build_image
	@set -e; \
	NAME="$(DOCKER_CONTAINER_NAME)"; \
	IMAGE="$(DOCKER_IMAGE_LATEST)"; \
	if [ -n "$$(docker ps -q -f name=^$${NAME}$$)" ]; then \
		echo "→ Container '$${NAME}' is running; opening a new shell"; \
		exec docker exec -it \
			--env TERM="$$TERM" --env COLORTERM="$$COLORTERM" \
			"$${NAME}" /usr/bin/zsh -l; \
	fi; \
	if [ -n "$$(docker ps -aq -f status=exited -f name=^$${NAME}$$)" ]; then \
		echo "→ Container '$${NAME}' exists but is stopped; starting…"; \
		docker start "$${NAME}" >/dev/null; \
		exec docker exec -it \
			--env TERM="$$TERM" --env COLORTERM="$$COLORTERM" \
			"$${NAME}" /usr/bin/zsh -l; \
	fi; \
	echo "--- Allowing local Docker container to access X server ---"; \
	xhost +SI:localuser:$(USER); \
	echo "→ No container named '$${NAME}'; creating a new one"; \
	set -x; \
	docker run -it \
		--name "$${NAME}" \
		-p 8765:8765 \
		-e DISPLAY="$(DISPLAY)" \
		-e QT_X11_NO_MITSHM=1 \
		-v /tmp/.X11-unix:/tmp/.X11-unix \
		-v "$(WORKSPACE_ROOT):/home/$(USER)/adore" \
		--device /dev/dri \
		"$$IMAGE" /usr/bin/zsh -l; \
	RET=$$?; set +x; \
	echo "--- Revoking X server access ---"; \
	xhost -SI:localuser:$(USER) || true; \
	exit $$RET

# Optional: stop the container and revoke X (use when you want to fully shut it down)
.PHONY: stop_cli
stop_cli:
	@set -e; \
	if [ -n "$$(docker ps -q -f name=^$(DOCKER_CONTAINER_NAME)$$)" ]; then \
		echo "→ Stopping container '$(DOCKER_CONTAINER_NAME)'"; \
		docker stop "$(DOCKER_CONTAINER_NAME)" >/dev/null; \
	fi; \
	echo "--- Revoking X server access ---"; \
	xhost -SI:localuser:$(USER) || true

	

# --- GUI app ---
gui:
	python3 tools/adore_gui.py

# --- Other tools ---
edit_roads:
	python3 tools/edit_roads.py

lichtblick:
	./tools/run_lichtblick.sh

# --- Save/Load Docker Images ---
save:
	mkdir -p $(WORKSPACE_ROOT)/build
	docker save $(DOCKER_IMAGE_TAGGED) > $(WORKSPACE_ROOT)/build/$(DOCKER_IMAGE_BASE)_$(IMAGE_TAG).tar
	@echo "Docker image saved to build/$(DOCKER_IMAGE_BASE)_$(IMAGE_TAG).tar"

load:
	docker load < $(WORKSPACE_ROOT)/build/$(DOCKER_IMAGE_BASE)_$(IMAGE_TAG).tar
	@echo "Docker image loaded from build/$(DOCKER_IMAGE_BASE)_$(IMAGE_TAG).tar"
