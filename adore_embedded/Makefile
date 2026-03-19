SHELL     := /bin/bash
MAKEFLAGS += --warn-undefined-variables --no-builtin-rules
.NOTPARALLEL:
.DEFAULT_GOAL := build

ROOT_DIR := $(shell dirname "$(realpath $(firstword $(MAKEFILE_LIST)))")
HOST_UID := $(shell id -u)
HOST_GID := $(shell id -g)

DOCKER_BUILDKIT ?= 1
ROS_DISTRO      ?= jazzy
OS_CODE_NAME    ?= noble
ARCH            ?= $(shell uname -m)
DOCKER_PLATFORM ?= linux/$(ARCH)

VENDOR_PATH      ?= $(ROOT_DIR)/../vendor
ROS2_WORKSPACE   ?= $(ROOT_DIR)/../ros2_workspace
ROS2_SRC         ?= $(ROS2_WORKSPACE)/src

SHORT_HASH        := $(shell git -C "$(ROOT_DIR)" rev-parse --short HEAD 2>/dev/null || echo "0000000")
REQUIREMENTS_HASH := $(shell \
    { find $(ROOT_DIR) -maxdepth 2 -type f \( -name "*.system" -o -name "*.pip3" -o -name "*.ppa" \) \
        ! -path "*/context/*" 2>/dev/null; \
      find $(ROS2_SRC) -type f \( -name "*.system" -o -name "*.pip3" -o -name "*.ppa" \) \
        2>/dev/null; } \
    | LC_ALL=C sort | xargs -r sha256sum 2>/dev/null | sha256sum | cut -c1-7 || echo "0000000")

IMAGE_NAME     := adore_embedded
IMAGE_TAG      := $(ARCH)_$(SHORT_HASH)_RH$(REQUIREMENTS_HASH)
IMAGE          := $(IMAGE_NAME):$(IMAGE_TAG)
CONTAINER_NAME := $(IMAGE_NAME)_$(IMAGE_TAG)

BUILD_DIR          := $(ROOT_DIR)/build/$(IMAGE_TAG)
CONTEXT_DIR        := $(ROOT_DIR)/context
IMAGE_ARCHIVE_NAME := $(IMAGE_NAME)_$(IMAGE_TAG).tar
IMAGE_ARCHIVE      := $(BUILD_DIR)/$(IMAGE_ARCHIVE_NAME)

.PHONY: build
build: _gather ## Build the image, compile the ROS2 workspace, and save to build/<tag>/
	@echo "=== Building $(IMAGE) ==="
	docker build \
	    --platform $(DOCKER_PLATFORM) \
	    --build-arg ROS_DISTRO=$(ROS_DISTRO) \
	    --build-arg OS_CODE_NAME=$(OS_CODE_NAME) \
	    --build-arg ARCH=$(ARCH) \
	    --build-arg SHORT_HASH=$(SHORT_HASH) \
	    --build-arg REQUIREMENTS_HASH=$(REQUIREMENTS_HASH) \
	    -t $(IMAGE) \
	    -f $(ROOT_DIR)/Dockerfile \
	    $(ROOT_DIR)
	@mkdir -p $(BUILD_DIR)
	@echo "=== Building ROS2 workspace inside container ==="
	@docker stop $(CONTAINER_NAME) 2>/dev/null || true
	@docker rm -f $(CONTAINER_NAME) 2>/dev/null || true
	docker run --detach \
	    --name $(CONTAINER_NAME) \
	    --platform $(DOCKER_PLATFORM) \
	    --network host \
	    --user "$(HOST_UID):$(HOST_GID)" \
	    --env-file "$(ROOT_DIR)/container.env" \
	    -e ROS_DISTRO=$(ROS_DISTRO) \
	    -v "$(ROS2_WORKSPACE):/ros2_workspace" \
	    $(IMAGE) \
	    sleep infinity
	docker exec --workdir /ros2_workspace $(CONTAINER_NAME) make build
	@docker stop $(CONTAINER_NAME)
	@docker rm -f $(CONTAINER_NAME)
	@echo "=== Saving $(IMAGE) → $(IMAGE_ARCHIVE) ==="
	docker save $(IMAGE) -o $(IMAGE_ARCHIVE)
	@cp -r "$(ROS2_WORKSPACE)" $(BUILD_DIR)/ros2_workspace
	@cp -r "$(ROOT_DIR)/../adore_scenarios" $(BUILD_DIR)/ros2_workspace/adore_scenarios
	@cp -r "$(CONTEXT_DIR)" $(BUILD_DIR)/ros2_workspace/context
	@$(MAKE) --no-print-directory _write_scripts \
	    _BUILD_DIR=$(BUILD_DIR) \
	    _IMAGE=$(IMAGE) \
	    _IMAGE_TAG=$(IMAGE_TAG) \
	    _IMAGE_ARCHIVE_NAME=$(IMAGE_ARCHIVE_NAME) \
	    _CONTAINER_NAME=$(CONTAINER_NAME)
	@echo "=== Done: $(BUILD_DIR) ==="

.PHONY: start
start: _ensure_loaded ## Start the container detached with the live workspace mounted
	@if docker ps --format "{{.Names}}" | grep -q "^$(CONTAINER_NAME)$$"; then \
	    echo "✓ Already running: $(CONTAINER_NAME)"; \
	else \
	    docker run --detach \
	        --name $(CONTAINER_NAME) \
	        --platform $(DOCKER_PLATFORM) \
	        --network host \
	        --user "$(HOST_UID):$(HOST_GID)" \
	        --env-file "$(ROOT_DIR)/container.env" \
	        -e ROS_DISTRO=$(ROS_DISTRO) \
	        -v "$(ROS2_WORKSPACE):/ros2_workspace" \
	        $(IMAGE) \
	        sleep infinity; \
	    echo "✓ Started: $(CONTAINER_NAME)"; \
	fi

.PHONY: stop
stop: ## Stop and remove the container
	@docker stop $(CONTAINER_NAME) 2>/dev/null || true
	@docker rm -f $(CONTAINER_NAME) 2>/dev/null || true
	@echo "✓ Stopped: $(CONTAINER_NAME)"

.PHONY: run
run: start ## Start the container detached (alias for start)

.PHONY: shell
shell: start ## Attach an interactive shell to the running container
	docker exec -it --workdir /ros2_workspace $(CONTAINER_NAME) /bin/bash

.PHONY: clean
clean: ## Remove image, build output, and build context
	docker rmi $(IMAGE) 2>/dev/null || true
	rm -rf $(ROOT_DIR)/build $(CONTEXT_DIR)

.PHONY: _ensure_loaded
_ensure_loaded:
	@if ! docker image inspect $(IMAGE) >/dev/null 2>&1; then \
	    if [ -f "$(IMAGE_ARCHIVE)" ]; then \
	        echo "Loading $(IMAGE_ARCHIVE)..."; \
	        docker load -i "$(IMAGE_ARCHIVE)"; \
	    else \
	        echo "ERROR: image $(IMAGE) not found. Run 'make build' first."; exit 1; \
	    fi \
	fi

.PHONY: _write_scripts
_write_scripts:
	@printf 'IMAGE=%s\nIMAGE_TAG=%s\nIMAGE_ARCHIVE_NAME=%s\nCONTAINER_NAME=%s\nDOCKER_PLATFORM=%s\nROS_DISTRO=%s\n' \
	    "$(_IMAGE)" "$(_IMAGE_TAG)" "$(_IMAGE_ARCHIVE_NAME)" "$(_CONTAINER_NAME)" \
	    "$(DOCKER_PLATFORM)" "$(ROS_DISTRO)" \
	    > $(_BUILD_DIR)/adore.env
	@cp $(ROOT_DIR)/scripts/load.sh  $(_BUILD_DIR)/load.sh  && chmod +x $(_BUILD_DIR)/load.sh
	@cp $(ROOT_DIR)/scripts/shell.sh $(_BUILD_DIR)/shell.sh && chmod +x $(_BUILD_DIR)/shell.sh
	@cp $(ROOT_DIR)/scripts/run.sh   $(_BUILD_DIR)/run.sh   && chmod +x $(_BUILD_DIR)/run.sh
	@cp $(ROOT_DIR)/scripts/stop.sh  $(_BUILD_DIR)/stop.sh  && chmod +x $(_BUILD_DIR)/stop.sh
	@cp $(ROOT_DIR)/scripts/build_ros_workspace.sh $(_BUILD_DIR)/build_ros_workspace.sh && chmod +x $(_BUILD_DIR)/build_ros_workspace.sh
	@cp $(ROOT_DIR)/container.env $(_BUILD_DIR)/container.env

.PHONY: _gather
_gather:
	@echo "=== Gathering requirements ==="
	@rm -rf $(CONTEXT_DIR)
	@mkdir -p $(CONTEXT_DIR)/vendor
	@{ find $(ROOT_DIR) -maxdepth 2 -type f -name "*.system" \
	        ! -path "*/context/*" 2>/dev/null; \
	     find $(ROS2_SRC) -type f -name "*.system" 2>/dev/null; } \
	    | LC_ALL=C sort \
	    | xargs -r grep -hv '^\s*#' \
	    | grep -v '^\s*$$' \
	    | LC_ALL=C sort -u \
	    > $(CONTEXT_DIR)/requirements.system || true
	@{ find $(ROOT_DIR) -maxdepth 2 -type f -name "*.pip3" \
	        ! -path "*/context/*" 2>/dev/null; \
	     find $(ROS2_SRC) -type f -name "*.pip3" 2>/dev/null; } \
	    | LC_ALL=C sort \
	    | xargs -r grep -hv '^\s*#' \
	    | grep -v '^\s*$$' \
	    | LC_ALL=C sort -u \
	    > $(CONTEXT_DIR)/requirements.pip3 || true
	@{ find $(ROOT_DIR) -maxdepth 2 -type f -name "*.ppa" \
	        ! -path "*/context/*" 2>/dev/null; \
	     find $(ROS2_SRC) -type f -name "*.ppa" 2>/dev/null; } \
	    | LC_ALL=C sort \
	    | xargs -r grep -hv '^\s*#' \
	    | grep '^ppa:' \
	    | LC_ALL=C sort -u \
	    > $(CONTEXT_DIR)/requirements.ppa || true
	@find "$(VENDOR_PATH)/build" -name '*.deb' 2>/dev/null \
	    | sort | xargs -r -I{} cp {} $(CONTEXT_DIR)/vendor/ || true
	@cp $(ROOT_DIR)/scripts/install_packages.sh  $(CONTEXT_DIR)/install_packages.sh  && chmod +x $(CONTEXT_DIR)/install_packages.sh
	@cp $(ROOT_DIR)/scripts/install_requirements.sh $(CONTEXT_DIR)/install_requirements.sh && chmod +x $(CONTEXT_DIR)/install_requirements.sh
	@echo "  system : $$(wc -l < $(CONTEXT_DIR)/requirements.system)"
	@echo "  pip3   : $$(wc -l < $(CONTEXT_DIR)/requirements.pip3)"
	@echo "  ppa    : $$(wc -l < $(CONTEXT_DIR)/requirements.ppa)"
	@echo "  debs   : $$(find $(CONTEXT_DIR)/vendor -name '*.deb' | wc -l)"
	@echo "=== Gather complete ==="
