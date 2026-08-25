.DEFAULT_GOAL := help

IMAGE_NAME    := weather_service_interface
IMAGE_TAG     := latest
ROS_DISTRO    := jazzy
OS_CODE_NAME  := noble
SAVE_FILE     := $(IMAGE_NAME).tar

CONFIG        := $(shell pwd)/config/weather_service_config.yaml
ROS_DOMAIN_ID := 0
ROS_HOME      := $(HOME)/.ros

DISPLAY       ?= $(DISPLAY)
XAUTH         ?= $(XAUTHORITY)
X11_SOCKET    := /tmp/.X11-unix

DOCKER_COMMON := docker run --rm \
	--network host \
	--env ROS_DOMAIN_ID=$(ROS_DOMAIN_ID) \
	--env ROS_HOME=/ros_home \
	--env FASTDDS_BUILTIN_TRANSPORTS=UDPv4 \
	--volume $(ROS_HOME):/ros_home \
	--volume $(CONFIG):/config/weather_service_config.yaml:ro

DOCKER_DISPLAY := --env DISPLAY=$(DISPLAY) \
	--env WEATHER_CONFIG_PATH=/config/weather_service_config.yaml \
	$(if $(XAUTH),--env XAUTHORITY=/tmp/.Xauthority --volume $(XAUTH):/tmp/.Xauthority:ro) \
	$(if $(wildcard $(X11_SOCKET)),--volume $(X11_SOCKET):$(X11_SOCKET))

DOCKER_RUN := $(DOCKER_COMMON) \
	$(IMAGE_NAME):$(IMAGE_TAG)

.PHONY: help
help:
	@echo "weather_service_interface"
	@echo ""
	@echo "Usage: make <target>"
	@echo ""
	@echo "Targets:"
	@echo "  build              Build the Docker image"
	@echo "  run                Run the weather service node"
	@echo "  run_visualizer     Run the weather service + visualizer (service logs to /tmp/weather_service.log)"
	@echo "  shell              Open a shell inside the container"
	@echo "  save               Save the Docker image to $(SAVE_FILE)"
	@echo "  load               Load the Docker image from $(SAVE_FILE)"
	@echo "  clean              Remove the Docker image and saved file"
	@echo ""
	@echo "Variables (override on the command line):"
	@echo "  CONFIG             Path to service config     (default: config/weather_service_config.yaml)"
	@echo "  ROS_DOMAIN_ID      ROS domain ID               (default: $(ROS_DOMAIN_ID))"
	@echo "  ROS_HOME           Host path for forecast logs (default: $(ROS_HOME))"
	@echo "  DISPLAY            X11 display for xterm       (default: \$$DISPLAY)"
	@echo "  XAUTH              Xauthority file for xterm   (default: \$$XAUTHORITY)"
	@echo "  ROS_DISTRO         ROS distribution             (default: $(ROS_DISTRO))"
	@echo "  OS_CODE_NAME       Ubuntu codename              (default: $(OS_CODE_NAME))"
	@echo "  IMAGE_TAG          Docker image tag             (default: $(IMAGE_TAG))"

.PHONY: build
build:
	docker build \
		--build-arg ROS_DISTRO=$(ROS_DISTRO) \
		--build-arg OS_CODE_NAME=$(OS_CODE_NAME) \
		-t $(IMAGE_NAME):$(IMAGE_TAG) .

.PHONY: run
run:
	$(DOCKER_RUN) ros2 launch weather_service_interface weather_service.launch.py \
		config_path:=/config/weather_service_config.yaml

# Service output is redirected to /tmp/weather_service.log so it does not
# corrupt the curses display. DOCKER_DISPLAY forwards X11 sockets and auth
# for xterm when visualizer.use_xterm is enabled in the config.
.PHONY: run_visualizer
run_visualizer:
	@$(DOCKER_RUN) ros2 launch weather_service_interface weather_service.launch.py \
		config_path:=/config/weather_service_config.yaml \
		>/tmp/weather_service.log 2>&1 & \
	SERVICE_PID=$$!; \
	trap "kill $$SERVICE_PID 2>/dev/null; wait $$SERVICE_PID 2>/dev/null" EXIT INT TERM; \
	docker run --rm -it \
		--network host \
		--env ROS_DOMAIN_ID=$(ROS_DOMAIN_ID) \
		--env ROS_HOME=/ros_home \
		--env FASTDDS_BUILTIN_TRANSPORTS=UDPv4 \
		--volume $(ROS_HOME):/ros_home \
		$(DOCKER_DISPLAY) \
		--volume $(CONFIG):/config/weather_service_config.yaml:ro \
		$(IMAGE_NAME):$(IMAGE_TAG) \
		ros2 run weather_service_interface weather_visualizer_node

.PHONY: shell
shell:
	$(DOCKER_RUN) bash

.PHONY: save
save:
	docker save $(IMAGE_NAME):$(IMAGE_TAG) -o $(SAVE_FILE)

.PHONY: load
load:
	docker load -i $(SAVE_FILE)

.PHONY: clean
clean:
	docker rmi $(IMAGE_NAME):$(IMAGE_TAG) || true
	rm -f $(SAVE_FILE)
