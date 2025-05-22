SHELL:=/bin/bash

.DEFAULT_GOAL := all

ROOT_DIR:=$(shell dirname "$(realpath $(firstword $(MAKEFILE_LIST)))")
OUTPUT_DIRECTORY=${ROOT_DIR}/output
SUBMODULES_PATH?=${ROOT_DIR}

.EXPORT_ALL_VARIABLES:
DOCKER_BUILDKIT?=1
DOCKER_CONFIG?=

ARCH?=$(shell uname -m)
DOCKER_PLATFORM?=linux/$(ARCH)
CROSS_COMPILE?=$(shell if [ "$(shell uname -m)" != "$(ARCH)" ]; then echo "true"; else echo "false"; fi)

PROJECT:=sumo
TAG := v1_22_0_${ARCH}

.PHONY: check_cross_compile_deps
check_cross_compile_deps:
	@if [ "$(CROSS_COMPILE)" = "true" ]; then \
        echo "Cross-compiling for $(ARCH) on $(shell uname -m)"; \
        if ! which qemu-$(ARCH)-static >/dev/null || ! docker buildx inspect $(ARCH)builder >/dev/null 2>&1; then \
            echo "Installing cross-compilation dependencies..."; \
            sudo apt-get update && sudo apt-get install -y qemu-user-static binfmt-support; \
            docker run --privileged --rm tonistiigi/binfmt --install $(ARCH); \
            if ! docker buildx inspect $(ARCH)builder >/dev/null 2>&1; then \
                docker buildx create --name $(ARCH)builder --driver docker-container --use; \
            fi; \
        fi; \
        export DOCKER_BUILDX=1; \
    fi

.PHONY: build
build: check_cross_compile_deps  ## Build Sumo
	@if [ "$(CROSS_COMPILE)" = "true" ]; then \
		echo "Cross-compiling ${PROJECT}:${TAG} for $(ARCH)..."; \
		docker buildx build --platform $(DOCKER_PLATFORM) \
			--tag ${PROJECT}:${TAG} \
			--build-arg PROJECT=${PROJECT} \
			--load .; \
	else \
		docker compose build; \
	fi
	@container_id=$$(docker create ${PROJECT}:${TAG}); \
	docker cp $$container_id:/tmp/sumo/build "${ROOT_DIR}/${PROJECT}"; \
	docker cp $$container_id:/tmp/sumo/bin "${ROOT_DIR}/${PROJECT}"; \
	docker rm $$container_id > /dev/null

.PHONY: clean
clean:  ## Clean build artifacts 
	git submodule deinit -f "${ROOT_DIR}/${PROJECT}"
	git submodule update --init --recursive "${ROOT_DIR}/${PROJECT}"
	docker rm $$(docker ps -a -q --filter "ancestor=${PROJECT}:${TAG}") --force 2> /dev/null || true
	docker rmi $$(docker images -q ${PROJECT}:${TAG}) --force 2> /dev/null || true
	docker rmi --force $$(docker images --filter "dangling=true" -q --no-trunc) 2> /dev/null || true

