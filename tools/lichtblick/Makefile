BUILD_DIR := .
DOCKER_IMAGE := lichtblick
OUTPUT_DIR := /build
MAKEFILE_DIR := $(shell dirname $(realpath $(firstword $(MAKEFILE_LIST))))
ASSET_DIRECTORY := "${MAKEFILE_DIR}/assets"
ASSET_MOUNTPOINT := /srv/assets
PORT ?= 8080

GITHUB_REPOSITORY ?= $(shell git config --get remote.origin.url | sed -E 's|^.*github\.com[:/]||; s|\.git$$||')
ARCH ?= $(shell uname -m)


LICHTBLICK_HASH := $(shell cat $(MAKEFILE_DIR)/Dockerfile.lichtblick $(MAKEFILE_DIR)/index.tsx 2>/dev/null | sha256sum | cut -c1-7)
LICHTBLICK_TAG := $(ARCH)_$(LICHTBLICK_HASH)
LICHTBLICK_IMAGE := $(DOCKER_IMAGE):$(LICHTBLICK_TAG)
LICHTBLICK_CONTAINER_NAME := lichtblick_$(LICHTBLICK_TAG)

GITHUB_REPO_LOWER := $(shell echo "$(GITHUB_REPOSITORY)" | tr '[:upper:]' '[:lower:]')
REGISTRY_IMAGE := ghcr.io/$(GITHUB_REPO_LOWER)/$(LICHTBLICK_IMAGE)

.PHONY: build
build:
	@$(MAKE) _try_pull_lichtblick || true
	@if ! docker image inspect $(LICHTBLICK_IMAGE) >/dev/null 2>&1; then \
		echo "Image not found in registry, building locally..."; \
		$(MAKE) build_force; \
	else \
		echo "✓ Using pulled image: $(LICHTBLICK_IMAGE)"; \
	fi

.PHONY: build_force
build_force:
	@echo "=== Building Lichtblick image ==="
	@echo "Tag: $(LICHTBLICK_TAG)"
	@echo "Hash: $(LICHTBLICK_HASH)"
	mkdir -p $(BUILD_DIR)
	docker build -f Dockerfile.lichtblick -t $(LICHTBLICK_IMAGE) .
	@echo "✓ Build complete: $(LICHTBLICK_IMAGE)"

.PHONY: _try_pull_lichtblick
_try_pull_lichtblick:
	@echo "=== Attempting to pull Lichtblick image from registry ==="
	@if docker pull "$(REGISTRY_IMAGE)" 2>/dev/null; then \
		docker tag "$(REGISTRY_IMAGE)" "$(LICHTBLICK_IMAGE)"; \
		echo "✓ Pulled from registry: $(LICHTBLICK_IMAGE)"; \
	else \
		echo "✗ Image not available in registry"; \
	fi

.PHONY: push_lichtblick
push_lichtblick:
	@echo "=== Pushing Lichtblick image to registry ==="
	@if docker image inspect "$(LICHTBLICK_IMAGE)" >/dev/null 2>&1; then \
		echo "Tagging and pushing: $(LICHTBLICK_IMAGE)"; \
		docker tag "$(LICHTBLICK_IMAGE)" "$(REGISTRY_IMAGE)"; \
		docker push "$(REGISTRY_IMAGE)"; \
		echo "✓ Pushed to registry: $(REGISTRY_IMAGE)"; \
	else \
		echo "✗ Image not found locally: $(LICHTBLICK_IMAGE)"; \
		echo "Run 'make build_force' first"; \
		exit 1; \
	fi

.PHONY: pull_lichtblick
pull_lichtblick: _try_pull_lichtblick
	@echo "✓ Pull complete"

.PHONY: start
start: stop
	@echo "=== Starting Lichtblick container ==="
	@if ! docker image inspect "$(LICHTBLICK_IMAGE)" >/dev/null 2>&1; then \
		echo "Image not found. Building..."; \
		$(MAKE) build; \
	fi
	@mkdir -p $(ASSET_DIRECTORY)
	docker run -it -d --rm --name $(LICHTBLICK_CONTAINER_NAME) \
		-p $(PORT):8080 \
		--volume $(ASSET_DIRECTORY):$(ASSET_MOUNTPOINT) \
		$(LICHTBLICK_IMAGE)
	@echo "Lichtblick started, navigate to http://localhost:$(PORT) for the web ui"
	@echo "http://localhost:8080//?ds=rosbridge-websocket&ds.url=ws://localhost:9090&ds=foxglove-websocket&layout=Default.json"



.PHONY: stop
stop:
	@echo "=== Stopping Lichtblick container ==="
	@docker stop $(LICHTBLICK_CONTAINER_NAME) 2>/dev/null || true
	@echo "✓ Container stopped"

.PHONY: info
info:
	@echo "=== Lichtblick Build Info ==="
	@echo "Architecture: $(ARCH)"
	@echo "Hash: $(LICHTBLICK_HASH)"
	@echo "Tag: $(LICHTBLICK_TAG)"
	@echo "Local image: $(LICHTBLICK_IMAGE)"
	@echo "Registry image: $(REGISTRY_IMAGE)"
	@echo "Container name: $(LICHTBLICK_CONTAINER_NAME)"
	@echo "GitHub repo: $(GITHUB_REPOSITORY)"
	@echo "Port: $(PORT)"
	@echo "Asset directory: $(ASSET_DIRECTORY)"
	@echo "Asset mountpoint: $(ASSET_MOUNTPOINT)"
	@echo ""
	@echo "Hash sources:"
	@if [ -f "$(MAKEFILE_DIR)/Dockerfile.lichtblick" ]; then \
		echo "  ✓ Dockerfile.lichtblick"; \
	else \
		echo "  ✗ Dockerfile.lichtblick (missing)"; \
	fi
	@if [ -f "$(MAKEFILE_DIR)/index.tsx" ]; then \
		echo "  ✓ index.tsx"; \
	else \
		echo "  ✗ index.tsx (missing)"; \
	fi
	@echo ""
	@if docker image inspect "$(LICHTBLICK_IMAGE)" >/dev/null 2>&1; then \
		echo "Local image status: ✓ exists"; \
	else \
		echo "Local image status: ✗ not built"; \
	fi
	@if docker ps --filter name=$(LICHTBLICK_CONTAINER_NAME) --format '{{.Names}}' | grep -q $(LICHTBLICK_CONTAINER_NAME); then \
		echo "Container status: ✓ running"; \
	else \
		echo "Container status: ✗ not running"; \
	fi

.PHONY: install
install: _install clean

.PHONY: _install
_install:
	python3 setup.py install

.PHONY: clean
clean:
	rm -rf ros2tools.egg-info build dist adore_model_checker/__pycache__
	rm -rf build
	docker rmi $(LICHTBLICK_IMAGE) --force 2>/dev/null || true

.PHONY: clean_all
clean_all: clean
	@echo "=== Cleaning all Lichtblick images ==="
	@docker images --format "{{.Repository}}:{{.Tag}}" | grep "^$(DOCKER_IMAGE):" | xargs -r docker rmi --force || true

.PHONY: help
help:
	@echo "=== Lichtblick Makefile Targets ==="
	@echo ""
	@echo "Build targets:"
	@echo "  build          Attempt to pull from registry, build only if not available"
	@echo "  build_force    Force a full local build, ignoring registry"
	@echo ""
	@echo "Run targets:"
	@echo "  start          Run the Lichtblick container (builds if needed)"
	@echo "  stop           Stop the running Lichtblick container"
	@echo ""
	@echo "Registry targets:"
	@echo "  push_lichtblick  Push local image to GitHub container registry"
	@echo "  pull_lichtblick  Pull image from GitHub container registry"
	@echo ""
	@echo "Utility targets:"
	@echo "  info           Show build configuration and status"
	@echo "  clean          Remove build artifacts and local image"
	@echo "  clean_all      Remove all Lichtblick images"
	@echo "  install        Install Python package"
	@echo "  help           Show this help message"
	@echo ""
	@echo "Configuration variables (can be overridden):"
	@echo "  PORT=$(PORT)               - Web UI port"
	@echo "  ASSET_DIRECTORY=$(ASSET_DIRECTORY)"
	@echo "  ASSET_MOUNTPOINT=$(ASSET_MOUNTPOINT)"
	@echo ""
	@echo "Current configuration:"
	@echo "  Image: $(LICHTBLICK_IMAGE)"
	@echo "  Registry: $(REGISTRY_IMAGE)"
	@echo "  Container: $(LICHTBLICK_CONTAINER_NAME)"
