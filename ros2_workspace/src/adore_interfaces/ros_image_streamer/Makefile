.DEFAULT_GOAL := help

IMAGE_NAME   := ros_image_streamer
IMAGE_TAG    := latest
ROS_DISTRO   := jazzy
OS_CODE_NAME := noble
SAVE_FILE    := $(IMAGE_NAME).tar

VIDEO_DEVICE  := /dev/video0
CONFIG        := $(shell pwd)/config/streamer_config.yaml
FFMPEG_HOST   := 127.0.0.1
FFMPEG_PORT   := 5000
FFMPEG_WIDTH  := 640
FFMPEG_HEIGHT := 480
FFMPEG_FPS    := 30
ROS_DOMAIN_ID := 0

DOCKER_RUN := docker run --rm \
	--network host \
	--device $(VIDEO_DEVICE):$(VIDEO_DEVICE) \
	--env DISPLAY=$(DISPLAY) \
	--env ROS_DOMAIN_ID=$(ROS_DOMAIN_ID) \
	--env FASTDDS_BUILTIN_TRANSPORTS=UDPv4 \
	--volume /tmp/.X11-unix:/tmp/.X11-unix \
	--volume $(CONFIG):/ros2_ws/src/ros_image_streamer/config/streamer_config.yaml:ro \
	$(IMAGE_NAME):$(IMAGE_TAG)

.PHONY: help
help:
	@echo "ros_image_streamer"
	@echo ""
	@echo "Usage: make <target>"
	@echo ""
	@echo "Targets:"
	@echo "  build            Build the Docker image"
	@echo "  run              Run streamer and viewer together"
	@echo "  run_streamer     Run the streaming node only"
	@echo "  run_viewer       Run the viewer node only"
	@echo "  run_ffmpeg       Start FFmpeg sending UDP MPEG-TS to $(FFMPEG_HOST):$(FFMPEG_PORT)"
	@echo "  save             Save the Docker image to $(SAVE_FILE)"
	@echo "  load             Load the Docker image from $(SAVE_FILE)"
	@echo "  clean            Remove the Docker image and saved file"
	@echo ""
	@echo "Variables (override on the command line):"
	@echo "  VIDEO_DEVICE     V4L2 device path         (default: $(VIDEO_DEVICE))"
	@echo "  CONFIG           Path to streamer config   (default: config/streamer_config.yaml)"
	@echo "  ROS_DOMAIN_ID    ROS domain ID             (default: $(ROS_DOMAIN_ID))"
	@echo "  FFMPEG_HOST      FFmpeg UDP target host     (default: $(FFMPEG_HOST))"
	@echo "  FFMPEG_PORT      FFmpeg UDP target port     (default: $(FFMPEG_PORT))"
	@echo "  FFMPEG_WIDTH     Capture width              (default: $(FFMPEG_WIDTH))"
	@echo "  FFMPEG_HEIGHT    Capture height             (default: $(FFMPEG_HEIGHT))"
	@echo "  FFMPEG_FPS       Capture framerate          (default: $(FFMPEG_FPS))"
	@echo "  ROS_DISTRO       ROS distribution           (default: $(ROS_DISTRO))"
	@echo "  OS_CODE_NAME     Ubuntu codename            (default: $(OS_CODE_NAME))"
	@echo "  IMAGE_TAG        Docker image tag           (default: $(IMAGE_TAG))"

.PHONY: build
build:
	docker build \
		--build-arg ROS_DISTRO=$(ROS_DISTRO) \
		--build-arg OS_CODE_NAME=$(OS_CODE_NAME) \
		-t $(IMAGE_NAME):$(IMAGE_TAG) .

.PHONY: run
run:
	xhost +local:docker
	$(DOCKER_RUN) ros2 launch ros_image_streamer streamer_and_viewer.launch.py

.PHONY: run_streamer
run_streamer:
	$(DOCKER_RUN) ros2 launch ros_image_streamer streamer.launch.py

.PHONY: run_viewer
run_viewer:
	xhost +local:docker
	$(DOCKER_RUN) ros2 launch ros_image_streamer viewer.launch.py

.PHONY: run_ffmpeg
run_ffmpeg:
	ffmpeg -f v4l2 \
		-framerate $(FFMPEG_FPS) \
		-video_size $(FFMPEG_WIDTH)x$(FFMPEG_HEIGHT) \
		-i $(VIDEO_DEVICE) \
		-vcodec libx264 \
		-preset ultrafast \
		-tune zerolatency \
		-f mpegts \
		"udp://$(FFMPEG_HOST):$(FFMPEG_PORT)?listen"

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
