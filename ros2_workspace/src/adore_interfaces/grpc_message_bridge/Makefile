IMAGE_NAME    ?= grpc_message_bridge
IMAGE_TAG     ?= latest
ROS_DISTRO    ?= jazzy
OS_CODE_NAME  ?= noble

BRIDGE_CONFIG ?= $(PWD)/config/bridge_config.yaml

GRPC_HOST ?= 0.0.0.0
GRPC_PORT ?= 50051

.PHONY: help
help:
	@echo "Usage: make <target>"
	@echo ""
	@echo "Targets:"
	@echo "  build         Build the bridge Docker image"
	@echo "  run           Start the bridge node container"
	@echo "  stop          Stop and remove running containers"
	@echo "  logs          Tail bridge container logs"
	@echo "  clean         Stop containers, remove image and prune build cache"
	@echo "  gen_proto     Regenerate Python stubs from ros_bridge.proto"
	@echo ""
	@echo "Overridable variables:"
	@echo "  IMAGE_NAME    $(IMAGE_NAME)"
	@echo "  IMAGE_TAG     $(IMAGE_TAG)"
	@echo "  ROS_DISTRO    $(ROS_DISTRO)"
	@echo "  OS_CODE_NAME  $(OS_CODE_NAME)"
	@echo "  BRIDGE_CONFIG $(BRIDGE_CONFIG)"
	@echo "  GRPC_HOST     $(GRPC_HOST)"
	@echo "  GRPC_PORT     $(GRPC_PORT)"

.PHONY: build
build:
	docker build \
		--build-arg ROS_DISTRO=$(ROS_DISTRO) \
		--build-arg OS_CODE_NAME=$(OS_CODE_NAME) \
		-t $(IMAGE_NAME):$(IMAGE_TAG) .

.PHONY: run
run:
	docker run --rm -d \
		--name grpc-bridge \
		--network host \
		-v $(BRIDGE_CONFIG):/config/bridge_config.yaml:ro \
		-e BRIDGE_CONFIG_PATH=/config/bridge_config.yaml \
		-e GRPC_HOST=$(GRPC_HOST) \
		-e GRPC_PORT=$(GRPC_PORT) \
		$(IMAGE_NAME):$(IMAGE_TAG)

.PHONY: stop
stop:
	docker stop grpc-bridge 2>/dev/null || true

.PHONY: logs
logs:
	docker logs -f grpc-bridge

.PHONY: clean
clean: stop
	docker rmi $(IMAGE_NAME):$(IMAGE_TAG) 2>/dev/null || true
	docker builder prune -f

.PHONY: gen_proto
gen_proto:
	python3 -m grpc_tools.protoc \
		-I grpc_message_bridge \
		--python_out=grpc_message_bridge \
		--grpc_python_out=grpc_message_bridge \
		grpc_message_bridge/ros_bridge.proto
	sed -i 's/^import ros_bridge_pb2/from . import ros_bridge_pb2/' \
		grpc_message_bridge/ros_bridge_pb2_grpc.py
