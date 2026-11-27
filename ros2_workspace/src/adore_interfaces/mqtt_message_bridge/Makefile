IMAGE      ?= mqtt_message_bridge
TAG        ?= latest
ROS_DISTRO ?= jazzy

.PHONY: build test test-host clean run shell

build:
	docker build --build-arg ROS_DISTRO=$(ROS_DISTRO) -t $(IMAGE):$(TAG) .

# Local suite against a throwaway broker. A real broker is tested with
# ./scripts/run_tests.sh --remote PATH.
test: build
	docker run --rm $(IMAGE):$(TAG) test

run: build
	docker run --rm -it --network host $(IMAGE):$(TAG) bridge

shell: build
	docker run --rm -it $(IMAGE):$(TAG) shell

test-host:
	./scripts/run_tests.sh

clean:
	-docker rmi -f $(IMAGE):$(TAG)
	rm -rf build install log
	find . -name '__pycache__' -type d -prune -exec rm -rf {} +
	find . -name '*.pyc' -delete
