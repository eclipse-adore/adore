ASSET_DIRECTORY:=$(CURDIR)/../../adore_scenarios/assets
ASSET_MOUNTPOINT:=/srv/assets

.EXPORT_ALL_VARIABLES:
DOCKER_CONFIG:=

.PHONY: build
build:
	docker build . -t lichtblick:latest -f Dockerfile.lichtblick

.PHONY: clean
clean:
	docker rmi --force lichtblick:latest > /dev/null 2>&1 || true

.PHONY: start
start:
	@echo "Starting Lichtblick..."
	docker stop -f lichtblick > /dev/null 2>&1 || true
	docker rm -f lichtblick > /dev/null 2>&1 || true
	echo ${ASSET_DIRECTORY}
	echo ${ASSET_MOUNTPOINT}
	docker run -it -d --rm --name lichtblick --network host --volume ${ASSET_DIRECTORY}:${ASSET_MOUNTPOINT} lichtblick:latest

	@echo "Lichtblick started, navigate to http://localhost:8080 for the web ui"

.PHONY: stop
stop:
	@echo "Stoping Lichtblick..."
	docker stop -f lichtblick > /dev/null 2>&1 || true
	docker rm -f lichtblick > /dev/null 2>&1 || true
	@echo "Lichtblick stopped"
