SHELL:=/bin/bash

.DEFAULT_GOAL := all

ROOT_DIR:=$(shell dirname "$(realpath $(firstword $(MAKEFILE_LIST)))")

MAKEFLAGS += --no-print-directory

.EXPORT_ALL_VARIABLES:
DOCKER_BUILDKIT?=1
DOCKER_CONFIG?=

USER := $(shell whoami)
UID := $(shell id -u)
GID := $(shell id -g)

.PHONY: build
build:
	docker build --no-cache . --tag ros2-humble-zenoh:latest

.PHONY: run
run:
	docker run -it --net=host \
        --rm \
        -e RMW_IMPLEMENTATION=rmw_zenoh_cpp \
        -v $(ROOT_DIR)/config.json5:/opt/ros/humble/share/rmw_zenoh_cpp/config/DEFAULT_RMW_ZENOH_SESSION_CONFIG.json5:ro \
        ros2-humble-zenoh \
        ros2 topic pub /zenoh_chatter std_msgs/msg/String "data: 'Hello, World'"
