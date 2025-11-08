SHELL:=/bin/bash

.DEFAULT_GOAL := help 

ROOT_DIR:=$(shell dirname "$(realpath $(firstword $(MAKEFILE_LIST)))")

.EXPORT_ALL_VARIABLES:
DOCKER_BUILDKIT?=1
DOCKER_CONFIG?=

USER := $(shell whoami)
UID := $(shell id -u)
GID := $(shell id -g)

.PHONY: help  
help:
	@printf "Usage: make \033[36m<target>\033[0m\n%s\n" "$$(awk 'BEGIN {FS = ":.*##"} /^[a-zA-Z0-9_-]+:.*?##/ { printf "  \033[36m%-10s\033[0m %s\n", $$1, $$2 } /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) } ' $(MAKEFILE_LIST) | sort | uniq)"

.PHONY: all
all: clean build 

.PHONY: build
build: build_gh-pages ## Build ADORe documentation 

.PHONY: update_submodules
update_submodules:
	git submodule update --init

.PHONY: build_gh-pages
build_gh-pages: build_mkdocs
	rm -rf docs
	mkdir -p docs
	cp -r mkdocs/site docs/mkdocs

.PHONY: build_mkdocs
build_mkdocs: update_submodules ## Build mkdocs 
	mkdir -p mkdocs/docs
	rm -rf mkdocs/docs/generated
	rm -rf mkdocs/site
	cp -r technical_reference_manual mkdocs/docs/technical_reference_manual
	python3 mkdocs/gen_docs.py
	cd mkdocs && mkdocs build

# ----------------------------------------------------------------------
# Serving docs locally (no nginx, just Python HTTP server)
# ----------------------------------------------------------------------

.PHONY: serve
serve: build ## Build and serve docs at http://localhost:8000
	cd docs && python3 -m http.server 8000

.PHONY: stop
stop: ## No-op (kept for compatibility)
	@true

.PHONY: publish_gh-pages
publish_gh-pages:
	bash publish_gh-pages.sh

.PHONY: publish
publish: publish_gh-pages ## Publish docs to gh-pages branch review the "publish.env" file before publishing

# ----------------------------------------------------------------------
# Auto-rebuild on changes (server runs in another terminal)
# ----------------------------------------------------------------------

.PHONY: watch
watch:
	while inotifywait -e modify -e create -e delete -r .; do \
        make build; \
    done

.PHONY: clean
clean:
	rm -rf docs || true
	rm -rf mkdocs/docs || true
	rm mkdocs/site -rf
	rm -rf technical_reference_manual/generated/

.PHONY: spellcheck
spellcheck: clean ## Start an interactive spell checking session with the tool aspell
	docker build -f Dockerfile.aspell -t aspell .
	docker run -it --rm -u "${UID}:${GID}" -v "$$(pwd):/mnt" aspell 'find /mnt/technical_reference_manual -name "**.md" -exec bash -c "aspell check --encoding=utf-8 --mode=markdown --home-dir=/mnt --personal=/mnt/.aspell.en.pws {}" \;'

.PHONY: lint
lint: clean ## Lint aka spell check the markdown files
	docker build -f Dockerfile.aspell -t aspell .
	docker run -u "${UID}:${GID}" -v $$(pwd):/mnt aspell:latest "python3 spellcheck.py"
