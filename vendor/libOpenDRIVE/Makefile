SHELL:=/bin/bash

.DEFAULT_GOAL := all

ROOT_DIR:=$(shell dirname "$(realpath $(firstword $(MAKEFILE_LIST)))")
OUTPUT_DIRECTORY=${ROOT_DIR}/output
SUBMODULES_PATH?=${ROOT_DIR}

.EXPORT_ALL_VARIABLES:
DOCKER_BUILDKIT?=1
DOCKER_CONFIG?=

PROJECT:=libopendrive
TAG := $(shell git rev-parse --short HEAD)

.PHONY: show-hash
show-hash:
	@echo "Git Short Hash: $(GIT_SHORT_HASH)"


.PHONY: build
build:
	docker build --network host \
                 --tag ${PROJECT}:${TAG} \
                 --build-arg PROJECT=${PROJECT} .
	docker cp $$(docker create --rm ${PROJECT}:${TAG}):/tmp/libOpenDRIVE/libOpenDRIVE/build "${ROOT_DIR}/libOpenDRIVE"

.PHONY: test
test: build
	mkdir -p ${OUTPUT_DIRECTORY}

.PHONY: run
run: build
	docker run -it ${PROJECT}:${TAG} /tmp/libOpenDRIVE/libOpenDRIVE/build/libOpenDRIVE

.PHONY: clean
clean:  ## Clean build artifacts 
	rm -rf "${ROOT_DIR}/${PROJECT}/build"
	rm -rf "${OUTPUT_DIRECTORY}"
	docker rm $$(docker ps -a -q --filter "ancestor=${PROJECT}:${TAG}") --force 2> /dev/null || true
	docker rmi $$(docker images -q ${PROJECT}:${TAG}) --force 2> /dev/null || true
	docker rmi --force $$(docker images --filter "dangling=true" -q --no-trunc) 2> /dev/null || true

