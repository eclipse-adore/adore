PACKAGE      ?= grpc_message_bridge
PROTO_ROOT   ?= $(PWD)/proto
PROTO_OUT    ?= $(PWD)/proto/generated

PROTO_SOURCES := \
  $(PROTO_ROOT)/messages/common.proto \
  $(PROTO_ROOT)/messages/events.proto \
  $(PROTO_ROOT)/messages/telemetry.proto \
  $(PROTO_ROOT)/messages/signaling.proto \
  $(PROTO_ROOT)/messages/commands.proto \
  $(PROTO_ROOT)/messages/config/sensors.proto \
  $(PROTO_ROOT)/messages/config/vehicle.proto \
  $(PROTO_ROOT)/vehicle/stream.proto \
  $(PROTO_ROOT)/client/notifications.proto \
  $(PROTO_ROOT)/client/stream.proto

IMAGE_NAME    ?= grpc_message_bridge
IMAGE_TAG     ?= latest
ROS_DISTRO    ?= jazzy
GRPC_HOST     ?= 0.0.0.0
GRPC_PORT     ?= 50051
BRIDGE_CONFIG ?= $(PWD)/config/bridge_config.yaml
SECRETS_ENV   ?= $(PWD)/.secrets.env

.PHONY: help
help:
	@echo "Targets:"
	@echo "  gen_proto   Regenerate Python stubs from proto/"
	@echo "  build       Build Docker image"
	@echo "  start       Start bridge container (alias for run)"
	@echo "  run         Start bridge container"
	@echo "  stop        Stop bridge container"
	@echo "  restart     Stop then start"
	@echo "  logs        Tail bridge container logs (Ctrl-C to exit)"
	@echo "  crash       Show logs from last exited container"
	@echo "  test        Run integration test suite inside the container"
	@echo "  inspect     Subscribe and print live data  (DURATION=30 VEHICLE=MV-001 TYPE=ALL)"
	@echo "              SCENARIO=N to run a single scenario"
	@echo "  clean       Stop + remove image"

.PHONY: gen_proto
gen_proto:
	@mkdir -p \
		$(PROTO_OUT)/messages/config \
		$(PROTO_OUT)/vehicle \
		$(PROTO_OUT)/client
	python3 -m grpc_tools.protoc \
		-I$(PROTO_ROOT) \
		$(shell python3 -m grpc_tools.protoc --version > /dev/null 2>&1 && \
		  python3 -c "import grpc_tools,os; print('-I'+os.path.join(os.path.dirname(grpc_tools.__file__),'_proto'))") \
		--python_out=$(PROTO_OUT) \
		--grpc_python_out=$(PROTO_OUT) \
		$(PROTO_SOURCES)
	@for d in $(PROTO_OUT) \
	           $(PROTO_OUT)/messages \
	           $(PROTO_OUT)/messages/config \
	           $(PROTO_OUT)/vehicle \
	           $(PROTO_OUT)/client; do \
		touch $$d/__init__.py; \
	done
	@echo "Stubs written to $(PROTO_OUT)"

.PHONY: build
build:
	docker build \
		--build-arg ROS_DISTRO=$(ROS_DISTRO) \
		-t $(IMAGE_NAME):$(IMAGE_TAG) .

.PHONY: start run
start run:
	@test -f $(SECRETS_ENV) || (echo "ERROR: $(SECRETS_ENV) not found"; exit 1)
	-docker stop grpc-bridge 2>/dev/null || true
	docker run --rm -d \
		--name grpc-bridge \
		--network host \
		--env-file $(SECRETS_ENV) \
		-v $(BRIDGE_CONFIG):/config/bridge_config.yaml:ro \
		-e BRIDGE_CONFIG_PATH=/config/bridge_config.yaml \
		-e GRPC_HOST=$(GRPC_HOST) \
		-e GRPC_PORT=$(GRPC_PORT) \
		$(IMAGE_NAME):$(IMAGE_TAG)

.PHONY: stop
stop:
	-docker stop grpc-bridge 2>/dev/null || true

.PHONY: restart
restart: stop start

.PHONY: logs
logs:
	docker logs -f grpc-bridge

.PHONY: crash
crash:
	docker logs $$(docker ps -aq --filter name=grpc-bridge | head -1) 2>&1 || \
	  echo "No exited grpc-bridge container found"

.PHONY: inspect
inspect:
	@test -f $(SECRETS_ENV) || (echo "ERROR: $(SECRETS_ENV) not found"; exit 1)
	docker run --rm -it \
		--network host \
		--env-file $(SECRETS_ENV) \
		-e PYTHONPATH=/ws/src/grpc_message_bridge/proto/generated \
		$(IMAGE_NAME):$(IMAGE_TAG) \
		python3 /ws/src/grpc_message_bridge/tools/test_integration.py \
		--inspect --duration $(or $(DURATION),30) $(if $(VEHICLE),--vehicle $(VEHICLE),) $(if $(TYPE),--type $(TYPE),)

.PHONY: test
test:
	@test -f $(SECRETS_ENV) || (echo "ERROR: $(SECRETS_ENV) not found"; exit 1)
	docker run --rm \
		--network host \
		--env-file $(SECRETS_ENV) \
		-e PYTHONPATH=/ws/src/grpc_message_bridge/proto/generated \
		$(IMAGE_NAME):$(IMAGE_TAG) \
		python3 /ws/src/grpc_message_bridge/tools/test_integration.py

.PHONY: clean
clean: stop
	docker rmi $(IMAGE_NAME):$(IMAGE_TAG) 2>/dev/null || true
	docker builder prune -f
