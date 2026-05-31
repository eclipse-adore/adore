IMAGE_NAME    ?= zenoh_message_bridge
IMAGE_TAG     ?= latest
ROUTER_IMAGE  ?= eclipse/zenoh:latest
ROUTER_NAME   ?= zenoh-router
ROS_DISTRO    ?= jazzy
OS_CODE_NAME  ?= noble

ZENOH_ROUTER_CONFIG  ?= $(PWD)/zenoh_router_config.json5
ZENOH_BRIDGE_CONFIG  ?= $(PWD)/zenoh_bridge_config.json5
BRIDGE_CONFIG        ?= $(PWD)/config/bridge_config.yaml

ROUTER_TCP_PORT ?= 7447
ROUTER_UDP_PORT ?= 7447

.PHONY: help
help:
	@echo "Usage: make <target>"
	@echo ""
	@echo "Targets:"
	@echo "  build         Build the bridge Docker image"
	@echo "  run           Start the Zenoh router then the bridge node"
	@echo "  run_bridge    Start only the bridge node container"
	@echo "  run_router    Start only the Zenoh router container"
	@echo "  stop          Stop and remove running containers"
	@echo "  logs_bridge   Tail bridge container logs"
	@echo "  logs_router   Tail router container logs"
	@echo "  clean         Stop containers, remove image and prune build cache"
	@echo ""
	@echo "Overridable variables:"
	@echo "  IMAGE_NAME          $(IMAGE_NAME)"
	@echo "  IMAGE_TAG           $(IMAGE_TAG)"
	@echo "  ROS_DISTRO          $(ROS_DISTRO)"
	@echo "  OS_CODE_NAME        $(OS_CODE_NAME)"
	@echo "  ROUTER_NAME         $(ROUTER_NAME)"
	@echo "  ZENOH_ROUTER_CONFIG $(ZENOH_ROUTER_CONFIG)"
	@echo "  ZENOH_BRIDGE_CONFIG $(ZENOH_BRIDGE_CONFIG)"
	@echo "  BRIDGE_CONFIG       $(BRIDGE_CONFIG)"
	@echo "  ROUTER_TCP_PORT     $(ROUTER_TCP_PORT)"
	@echo "  ROUTER_UDP_PORT     $(ROUTER_UDP_PORT)"

.PHONY: build
build:
	docker build \
		--build-arg ROS_DISTRO=$(ROS_DISTRO) \
		--build-arg OS_CODE_NAME=$(OS_CODE_NAME) \
		-t $(IMAGE_NAME):$(IMAGE_TAG) .

.PHONY: run
run: run_router run_bridge

.PHONY: run_router
run_router:
	docker run --rm -d \
		--name $(ROUTER_NAME) \
		--network host \
		-v $(ZENOH_ROUTER_CONFIG):/etc/zenoh/router_config.json5:ro \
		$(ROUTER_IMAGE) \
		--config /etc/zenoh/router_config.json5

.PHONY: run_bridge
run_bridge:
	docker run --rm -d \
		--name zenoh-bridge \
		--network host \
		-v $(ZENOH_BRIDGE_CONFIG):/config/zenoh_bridge_config.json5:ro \
		-v $(BRIDGE_CONFIG):/config/bridge_config.yaml:ro \
		-e ZENOH_CONFIG_PATH=/config/zenoh_bridge_config.json5 \
		-e BRIDGE_CONFIG_PATH=/config/bridge_config.yaml \
		$(IMAGE_NAME):$(IMAGE_TAG)

.PHONY: stop
stop:
	docker stop $(ROUTER_NAME) 2>/dev/null || true
	docker stop zenoh-bridge 2>/dev/null || true

.PHONY: logs_bridge
logs_bridge:
	docker logs -f zenoh-bridge

.PHONY: logs_router
logs_router:
	docker logs -f $(ROUTER_NAME)

.PHONY: clean
clean: stop
	docker rmi $(IMAGE_NAME):$(IMAGE_TAG) 2>/dev/null || true
	docker builder prune -f
