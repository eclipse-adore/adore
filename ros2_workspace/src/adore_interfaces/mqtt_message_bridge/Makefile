IMAGE      ?= mqtt_message_bridge
TAG        ?= latest
ROS_DISTRO ?= jazzy

.PHONY: build test test-offline test-host clean run shell

build:
	docker build --build-arg ROS_DISTRO=$(ROS_DISTRO) -t $(IMAGE):$(TAG) .

# Local suite against a throwaway broker, then the real broker: reachability,
# TLS, auth, live NMEA data and a mock solbox notification through to ROS.
test: build
	docker run --rm $(IMAGE):$(TAG) test

# Local suite only, for machines without egress to the broker.
test-offline: build
	docker run --rm $(IMAGE):$(TAG) test --no-remote

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
