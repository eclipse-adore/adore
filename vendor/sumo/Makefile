SHELL:=/bin/bash

.DEFAULT_GOAL := all

ROOT_DIR:=$(shell dirname "$(realpath $(firstword $(MAKEFILE_LIST)))")
OUTPUT_DIRECTORY=${ROOT_DIR}/output
SUBMODULES_PATH?=${ROOT_DIR}

.EXPORT_ALL_VARIABLES:
DOCKER_BUILDKIT?=1
DOCKER_CONFIG?=

PROJECT:=sumo
TAG := v1_22_0

.PHONY: build
build:
	docker compose build
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

