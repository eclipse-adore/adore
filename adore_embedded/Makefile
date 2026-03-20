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
PACKAGES_DIR       := $(ROOT_DIR)/packages
CONTEXT_DIR        := $(ROOT_DIR)/context
IMAGE_ARCHIVE_NAME := $(IMAGE_NAME)_$(IMAGE_TAG).tar
IMAGE_ARCHIVE      := $(BUILD_DIR)/$(IMAGE_ARCHIVE_NAME)

.PHONY: help
help: ## Show this help
	@printf "\n\033[1mTargets:\033[0m\n"
	@grep -E '^[a-zA-Z][a-zA-Z0-9_-]*:.*##' $(MAKEFILE_LIST) \
	    | awk 'BEGIN {FS = ":.*##"}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'
	@printf "\n"

.PHONY: build
build: _gather ## Build the image, compile the ROS2 workspace via BuildKit, and save to build/<tag>/
	@echo "=== Building $(IMAGE) ==="
	cd ${VENDOR_PATH} && make build
	docker build \
	    --platform $(DOCKER_PLATFORM) \
	    --build-arg ROS_DISTRO=$(ROS_DISTRO) \
	    --build-arg OS_CODE_NAME=$(OS_CODE_NAME) \
	    --build-arg ARCH=$(ARCH) \
	    --build-arg SHORT_HASH=$(SHORT_HASH) \
	    --build-arg REQUIREMENTS_HASH=$(REQUIREMENTS_HASH) \
	    --build-context ros2_workspace=$(ROS2_WORKSPACE) \
	    --build-context adore_scenarios=$(ROOT_DIR)/../adore_scenarios \
	    --target runtime \
	    -t $(IMAGE) \
	    -f $(ROOT_DIR)/Dockerfile \
	    $(ROOT_DIR)
	@mkdir -p $(BUILD_DIR)
	@echo "=== Extracting built workspace from image ==="
	@cid=$$(docker create --platform $(DOCKER_PLATFORM) $(IMAGE) /bin/true); \
	    docker cp "$$cid":/ros2_workspace_dist/. $(BUILD_DIR)/ros2_workspace/; \
	    docker rm "$$cid"
	@cp -r "$(CONTEXT_DIR)" $(BUILD_DIR)/ros2_workspace/context
	@echo "=== Saving $(IMAGE) → $(IMAGE_ARCHIVE).gz ==="
	docker save $(IMAGE) | gzip > $(IMAGE_ARCHIVE).gz
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

.PHONY: package
package: ## Save the current build output as a tar.gz in packages/
	@if [ ! -d "$(BUILD_DIR)" ]; then \
	    echo "ERROR: No build output at $(BUILD_DIR). Run 'make build' first."; exit 1; \
	fi
	@mkdir -p $(PACKAGES_DIR)
	@PKG=$(PACKAGES_DIR)/$(IMAGE_NAME)_$(IMAGE_TAG).tar.gz; \
	echo "=== Packaging $(BUILD_DIR) → $$PKG ==="; \
	tar -czf "$$PKG" -C "$(ROOT_DIR)/build" "$(IMAGE_TAG)"; \
	echo "=== Saved: $$PKG ==="

.PHONY: bundle
BUNDLE_NAME := $(IMAGE_NAME)_$(IMAGE_TAG)_bundle
BUNDLE_DIR  := $(PACKAGES_DIR)/$(BUNDLE_NAME)
bundle: ## Create a self-contained Docker-free rootfs bundle in packages/
	@if ! docker image inspect $(IMAGE) >/dev/null 2>&1; then \
	    echo "ERROR: Image $(IMAGE) not found. Run 'make build' first."; exit 1; \
	fi
	@if [ ! -d "$(BUILD_DIR)/ros2_workspace" ]; then \
	    echo "ERROR: No workspace at $(BUILD_DIR)/ros2_workspace. Run 'make build' first."; exit 1; \
	fi
	@mkdir -p $(PACKAGES_DIR)
	@echo "=== Creating bundle → $(BUNDLE_DIR).tar.gz ==="
	@rm -rf $(BUNDLE_DIR) && mkdir -p $(BUNDLE_DIR)/rootfs
	@echo "  Exporting rootfs (this may take a while)..."
	@cid=$$(docker create --platform $(DOCKER_PLATFORM) $(IMAGE) /bin/true); \
	    docker export "$$cid" | tar -x -C $(BUNDLE_DIR)/rootfs; \
	    docker rm "$$cid"
	@cp -r $(BUILD_DIR)/ros2_workspace $(BUNDLE_DIR)/ros2_workspace
	@cp $(ROOT_DIR)/container.env $(BUNDLE_DIR)/container.env
	@printf 'ROS_DISTRO=%s\nDOCKER_PLATFORM=%s\n' "$(ROS_DISTRO)" "$(DOCKER_PLATFORM)" \
	    > $(BUNDLE_DIR)/bundle.env
	@cp $(ROOT_DIR)/scripts/bundle_run.sh   $(BUNDLE_DIR)/run.sh   && chmod +x $(BUNDLE_DIR)/run.sh
	@cp $(ROOT_DIR)/scripts/bundle_shell.sh $(BUNDLE_DIR)/shell.sh && chmod +x $(BUNDLE_DIR)/shell.sh
	@cp $(ROOT_DIR)/scripts/bundle_inner.sh $(BUNDLE_DIR)/.bundle_inner.sh && chmod +x $(BUNDLE_DIR)/.bundle_inner.sh
	@echo "  Compressing..."
	@tar -czf $(BUNDLE_DIR).tar.gz -C $(PACKAGES_DIR) $(BUNDLE_NAME)
	@rm -rf $(BUNDLE_DIR)
	@echo "=== Bundle: $(BUNDLE_DIR).tar.gz ==="

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
	@cp $(ROOT_DIR)/scripts/bundle_run.sh   $(_BUILD_DIR)/bundle_run.sh   && chmod +x $(_BUILD_DIR)/bundle_run.sh
	@cp $(ROOT_DIR)/scripts/bundle_shell.sh $(_BUILD_DIR)/bundle_shell.sh && chmod +x $(_BUILD_DIR)/bundle_shell.sh
	@cp $(ROOT_DIR)/scripts/bundle_inner.sh $(_BUILD_DIR)/.bundle_inner.sh && chmod +x $(_BUILD_DIR)/.bundle_inner.sh
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
