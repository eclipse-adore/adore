# Use zsh as the shell
set shell := ["/bin/bash", "-c"]

# -------------------------------------------------------------------
# Global paths & environment
# -------------------------------------------------------------------

# Root of the repo (directory containing this Justfile)
export WORKSPACE_ROOT := justfile_directory()

# Colcon workspace dir (always .colcon_workspace under repo root)
export COLCON_WS_ROOT := WORKSPACE_ROOT + "/.colcon_workspace"

# Documentation root
export DOCS_ROOT := WORKSPACE_ROOT + "/documentation"

# Default ROS distro; can be overridden from the environment
export ROS_DISTRO := env('ROS_DISTRO', 'jazzy')

# Script to set up colcon_workspace/src symlinks
export SETUP_COLCON_SCRIPT := ".docker/scripts/setup_colcon_src.sh"

# Helpers: use shell variables and command substitution, no {{...}} inside
source_ros := 'source /opt/ros/$ROS_DISTRO/setup.zsh; if [ -f install/local_setup.zsh ]; then source install/local_setup.zsh || true; fi'
colcon_cmd := 'colcon build --parallel-workers $(nproc)'

# Host uid/gid for docker -u in docs_spellcheck/docs_lint
uid := `id -u`
gid := `id -g`


# Default target
default: dev

help:
    @just --list

# -------------------------------------------------------------------
# Symlink setup for colcon workspace
# -------------------------------------------------------------------
setup_colcon_src:
    cd "$WORKSPACE_ROOT" && \
    if [ -x "$SETUP_COLCON_SCRIPT" ]; then \
        echo "--- Ensuring colcon_workspace/src symlinks are set up ---"; \
        "$SETUP_COLCON_SCRIPT"; \
    else \
        echo "ERROR: $SETUP_COLCON_SCRIPT not found or not executable" >&2; \
        exit 1; \
    fi

# -------------------------------------------------------------------
# Docker-backed targets (dev image)
# -------------------------------------------------------------------
build_dev:
    cd "$WORKSPACE_ROOT" && .docker/scripts/build_image.sh

# Dev container: build + run
dev: setup_colcon_src
    cd "$WORKSPACE_ROOT" && .docker/scripts/run_dev.sh

clean_images:
    cd "$WORKSPACE_ROOT" && .docker/scripts/clean_images.sh

# Clean only the colcon workspace build artifacts
clean_ws:
    rm -rf "$COLCON_WS_ROOT/build" "$COLCON_WS_ROOT/install" "$COLCON_WS_ROOT/log"

# Full clean: docker images + workspace artifacts
clean: clean_images clean_ws
    echo "--- Cleaned docker images and .colcon_workspace build artifacts ---"

# Clean workspace build + rebuild (host colcon)
clean_build: clean_ws build

# Ensure symlinks also exist when dropping into the dev container
cli: setup_colcon_src
    cd "$WORKSPACE_ROOT" && .docker/scripts/cli.sh

stop_cli:
    cd "$WORKSPACE_ROOT" && .docker/scripts/stop_cli.sh

save:
    cd "$WORKSPACE_ROOT" && .docker/scripts/save_image.sh

load:
    cd "$WORKSPACE_ROOT" && .docker/scripts/load_image.sh

# -------------------------------------------------------------------
# Local tools (always run from repo root)
# -------------------------------------------------------------------
gui:
    cd "$WORKSPACE_ROOT" && python3 tools/adore_gui.py

edit_roads:
    cd "$WORKSPACE_ROOT" && python3 tools/edit_roads.py

lichtblick:
    cd "$WORKSPACE_ROOT" && ./tools/run_lichtblick.sh

# -------------------------------------------------------------------
# CI helpers (use the CI image under the hood)
# -------------------------------------------------------------------
# CI-style tests inside Docker image
test: setup_colcon_src
    cd "$WORKSPACE_ROOT" && .docker/scripts/run_tests.sh

docs: setup_colcon_src
    cd "$WORKSPACE_ROOT" && .docker/scripts/run_docs.sh

# Convenience: full CI locally (Docker-based)
ci: test docs

# -------------------------------------------------------------------
# Host colcon builds in .colcon_workspace (no Docker)
# -------------------------------------------------------------------

# Build adore_scenarios subset
build:
    cd "$COLCON_WS_ROOT" && {{source_ros}} && \
    {{colcon_cmd}} --packages-select `colcon list --base-paths src adore_scenarios --names-only`

# Run colcon tests locally on host (to distinguish from Docker CI tests)
test_ws:
    cd "$COLCON_WS_ROOT" && {{source_ros}} && \
    colcon test \
      --packages-skip `colcon list --base-paths src/vendor --names-only`; \
    colcon test-result --verbose

# Forcefully kill any lingering ROS 2 or colcon processes
force_kill_ros2:
    @echo "Forcefully killing lingering ROS 2 processes..."
    -pkill -9 -f ros2 || echo "No ros2 nodes running."
    -pkill -9 -f rclpy || echo "No rclpy nodes running."
    -pkill -9 -f launch || echo "No launch processes running."
    -pkill -9 -f colcon || echo "No colcon processes running."
    @echo "Done."

# Build vendor packages in adore_scenarios selectively
build_scenarios:
    cd "$COLCON_WS_ROOT" && {{source_ros}} && \
    {{colcon_cmd}} --packages-select `colcon list --base-paths adore_scenarios --names-only`

# Build library packages in adore_conversions selectively
build_conversions:
    cd "$COLCON_WS_ROOT" && {{source_ros}} && \
    {{colcon_cmd}} --packages-select `colcon list --base-paths src/conversions --names-only`

# Build library packages in libraries selectively
build_libraries:
    cd "$COLCON_WS_ROOT" && {{source_ros}} && \
    {{colcon_cmd}} --packages-select `colcon list --base-paths src/libraries --names-only`

# Build library packages in nodes selectively
build_nodes:
    cd "$COLCON_WS_ROOT" && {{source_ros}} && \
    {{colcon_cmd}} --packages-select `colcon list --base-paths src/nodes --names-only`

# Build library packages in ros2_messages selectively
build_messages:
    cd "$COLCON_WS_ROOT" && {{source_ros}} && \
    {{colcon_cmd}} --packages-select `colcon list --base-paths src/ros2_messages --names-only`

# Build vendor packages in vendor selectively
build_vendor:
    cd "$COLCON_WS_ROOT" && {{source_ros}} && \
    {{colcon_cmd}} --packages-select `colcon list --base-paths src/vendor --names-only`


# -------------------------------------------------------------------
# Documentation (mkdocs in documentation/)
# -------------------------------------------------------------------

# Equivalent of "all: clean build"
docs_all: docs_clean docs_build

# Equivalent of build_mkdocs
docs_build_mkdocs:
    cd "$DOCS_ROOT" && \
    mkdir -p mkdocs/docs && \
    rm -rf mkdocs/docs/generated mkdocs/site && \
    cp -r technical_reference_manual mkdocs/docs/technical_reference_manual && \
    python3 mkdocs/gen_docs.py && \
    cd mkdocs && mkdocs build

# Equivalent of build_gh-pages (and Makefile "build")
docs_build: docs_build_mkdocs
    cd "$DOCS_ROOT" && \
    rm -rf docs && \
    mkdir -p docs && \
    cp -r mkdocs/site docs/mkdocs

# Build + serve docs at http://localhost:8000
docs_serve: docs_build
    cd "$DOCS_ROOT/docs" && python3 -m http.server 8000

# Publish to gh-pages
docs_publish_gh_pages:
    cd "$DOCS_ROOT" && bash publish_gh-pages.sh

# Wrapper for publish_gh-pages
docs_publish: docs_publish_gh_pages
    @echo "Review documentation/publish.env before publishing."

# Watch for changes and rebuild docs (needs inotify-tools)
docs_watch:
    cd "$DOCS_ROOT" && \
    while inotifywait -e modify -e create -e delete -r .; do \
        just docs_build; \
    done

# Clean generated docs
docs_clean:
    cd "$DOCS_ROOT" && \
    rm -rf docs mkdocs/docs mkdocs/site technical_reference_manual/generated/

# Interactive spell checking via aspell container
docs_spellcheck: docs_clean
    cd "$DOCS_ROOT" && \
    docker build -f Dockerfile.aspell -t aspell . && \
    docker run -it --rm -u "{{uid}}:{{gid}}" -v "$PWD:/mnt" aspell \
      bash -lc 'find /mnt/technical_reference_manual -name "*.md" -exec aspell check --encoding=utf-8 --mode=markdown --home-dir=/mnt --personal=/mnt/.aspell.en.pws {} \;'

# Lint / non-interactive spellcheck
docs_lint: docs_clean
    cd "$DOCS_ROOT" && \
    docker build -f Dockerfile.aspell -t aspell . && \
    docker run -u "{{uid}}:{{gid}}" -v "$PWD:/mnt" aspell:latest python3 spellcheck.py

