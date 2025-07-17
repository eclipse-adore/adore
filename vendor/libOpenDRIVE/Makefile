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

PROJECT:=libopendrive
TAG := $(shell git rev-parse --short HEAD)_${ARCH}

.PHONY: show-hash
show-hash:
	@echo "Git Short Hash: $(GIT_SHORT_HASH)"

.PHONY: check_cross_compile_deps
check_cross_compile_deps:
	@if [ "$(CROSS_COMPILE)" = "true" ]; then \
        echo "Cross-compiling for $(ARCH) on $(shell uname -m)"; \
        if ! which qemu-$(ARCH)-static >/dev/null || ! docker buildx inspect $(ARCH)builder >/dev/null 2>&1; then \
            echo "Installing cross-compilation dependencies..."; \
            sudo apt-get update && sudo apt-get install -y qemu qemu-user-static binfmt-support; \
            docker run --privileged --rm tonistiigi/binfmt --install $(ARCH); \
            if ! docker buildx inspect $(ARCH)builder >/dev/null 2>&1; then \
                docker buildx create --name $(ARCH)builder --driver docker-container --use; \
            fi; \
        fi; \
    fi

.PHONY: build
build: check_cross_compile_deps
	@if [ "$(CROSS_COMPILE)" = "true" ]; then \
        echo "Cross-compiling ${PROJECT}:${TAG} for $(ARCH)..."; \
        docker buildx build \
            --builder=default \
            --platform=$(DOCKER_PLATFORM) \
            --tag ${PROJECT}:${TAG} \
            --build-arg ARCH=$(ARCH) \
            --build-arg PROJECT=$(PROJECT) \
            --load .; \
    else \
        docker build --network host \
            --tag ${PROJECT}:${TAG} \
            --build-arg ARCH=$(ARCH) \
            --build-arg PROJECT=$(PROJECT) .; \
    fi
	docker cp $$(docker create --rm ${PROJECT}:${TAG}):/tmp/libOpenDRIVE/libOpenDRIVE/build "${ROOT_DIR}/libOpenDRIVE"

.PHONY: test
test: build
	mkdir -p ${OUTPUT_DIRECTORY}

.PHONY: run
run: build
	docker run -it ${PROJECT}:${TAG} /tmp/libOpenDRIVE/libOpenDRIVE/build/libOpenDRIVE

.PHONY: clean
clean:  ## Clean build artifacts 
	rm -rf "libOpenDRIVE/build"
	rm -rf "${OUTPUT_DIRECTORY}"
	docker rm $$(docker ps -a -q --filter "ancestor=${PROJECT}:${TAG}") --force 2> /dev/null || true
	docker rmi $$(docker images -q ${PROJECT}:${TAG}) --force 2> /dev/null || true
	docker rmi --force $$(docker images --filter "dangling=true" -q --no-trunc) 2> /dev/null || true

