# Use bash as the shell
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

# Show all available recipes
help:
    @just --list

# -------------------------------------------------------------------
# Symlink setup for colcon workspace
# -------------------------------------------------------------------

# Ensure .colcon_workspace/src symlinks are up to date
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

# Build the dev Docker image (adore_dev)
build_dev:
    cd "$WORKSPACE_ROOT" && .docker/scripts/build_dev.sh

# Start or attach to the ADORe dev container
dev: setup_colcon_src
    cd "$WORKSPACE_ROOT" && .docker/scripts/run_dev.sh

# Remove local ADORe Docker images
clean_images:
    cd "$WORKSPACE_ROOT" && .docker/scripts/clean_images.sh

# Remove .colcon_workspace build/install/log directories
clean_ws:
    rm -rf "$COLCON_WS_ROOT/build" "$COLCON_WS_ROOT/install" "$COLCON_WS_ROOT/log"

# Full clean: Docker images + .colcon_workspace artifacts
clean: clean_images clean_ws
    echo "--- Cleaned docker images and .colcon_workspace build artifacts ---"

# Clean workspace and rebuild (host colcon)
clean_build: clean_ws build

# Open an interactive CLI shell in the dev container
cli: setup_colcon_src
    cd "$WORKSPACE_ROOT" && .docker/scripts/cli.sh

# Stop the dev container started by cli/dev
stop_cli:
    cd "$WORKSPACE_ROOT" && .docker/scripts/stop_cli.sh

# Save dev/CI images to tarball(s)
save:
    cd "$WORKSPACE_ROOT" && .docker/scripts/save_image.sh

# Load dev/CI images from tarball(s)
load:
    cd "$WORKSPACE_ROOT" && .docker/scripts/load_image.sh

# -------------------------------------------------------------------
# Local tools (always run from repo root)
# -------------------------------------------------------------------

# Launch the ADORe GUI (scenario launcher)
gui:
    cd "$WORKSPACE_ROOT" && python3 tools/adore_gui.py

# Run the road network editor
edit_roads:
    cd "$WORKSPACE_ROOT" && python3 tools/edit_roads.py

# Run the Lichtblick visualization wrapper
lichtblick:
    cd "$WORKSPACE_ROOT" && ./tools/run_lichtblick.sh

# -------------------------------------------------------------------
# CI helpers (use the CI image under the hood)
# -------------------------------------------------------------------

# Run CI-style tests inside the CI Docker image
test: setup_colcon_src
    cd "$WORKSPACE_ROOT" && .docker/scripts/run_tests.sh

# Build documentation inside the CI Docker image
docs: setup_colcon_src
    cd "$WORKSPACE_ROOT" && .docker/scripts/run_docs.sh

# Convenience: run tests and docs (full CI) locally
ci: test docs

# -------------------------------------------------------------------
# ADORe API control (via tools/adore_api/adore_api.sh)
# -------------------------------------------------------------------

# Start adore api server
api_start:
    cd "$WORKSPACE_ROOT" && \
    source tools/adore_api/adore_api.sh && \
    start_adore_api

# Stop adore api server
api_stop:
    cd "$WORKSPACE_ROOT" && \
    source tools/adore_api/adore_api.sh && \
    stop_adore_api

# Restart adore api server
api_restart:
    cd "$WORKSPACE_ROOT" && \
    source tools/adore_api/adore_api.sh && \
    restart_adore_api

# Check adore api server status
api_status:
    cd "$WORKSPACE_ROOT" && \
    source tools/adore_api/adore_api.sh && \
    status_adore_api


# -------------------------------------------------------------------
# Host colcon builds in .colcon_workspace (no Docker)
# -------------------------------------------------------------------

# Build the entire workspace locally (host colcon)
build:
    cd "$COLCON_WS_ROOT" && {{source_ros}} && \
    {{colcon_cmd}}

# Run colcon tests locally (host), skipping vendor + ros-carla-msgs
test_ws:
    cd "$COLCON_WS_ROOT" && {{source_ros}} && \
    colcon test \
      --packages-skip `colcon list --base-paths src/vendor  src/ros2_messages/ros-carla-msgs --names-only`; \
    colcon test-result --verbose

# Kill lingering ROS 2 / colcon processes (host + container aware script)
force_kill_ros2:
    cd "$WORKSPACE_ROOT" && .docker/scripts/force_kill_ros2.sh

# Build adore_scenarios packages only (host colcon)
build_scenarios:
    cd "$COLCON_WS_ROOT" && {{source_ros}} && \
    {{colcon_cmd}} --packages-select `colcon list --base-paths src/adore_scenarios --names-only`

# Build conversions packages only (host colcon)
build_conversions:
    cd "$COLCON_WS_ROOT" && {{source_ros}} && \
    {{colcon_cmd}} --packages-select `colcon list --base-paths src/conversions --names-only`

# Build library packages only (host colcon)
build_libraries:
    cd "$COLCON_WS_ROOT" && {{source_ros}} && \
    {{colcon_cmd}} --packages-select `colcon list --base-paths src/libraries --names-only`

# Build node packages only (host colcon)
build_nodes:
    cd "$COLCON_WS_ROOT" && {{source_ros}} && \
    {{colcon_cmd}} --packages-select `colcon list --base-paths src/nodes --names-only`

# Build ros2_messages packages only (host colcon)
build_messages:
    cd "$COLCON_WS_ROOT" && {{source_ros}} && \
    {{colcon_cmd}} --packages-select `colcon list --base-paths src/ros2_messages --names-only`

# Build vendor packages only (host colcon)
build_vendor:
    cd "$COLCON_WS_ROOT" && {{source_ros}} && \
    {{colcon_cmd}} --packages-select `colcon list --base-paths src/vendor --names-only`

# -------------------------------------------------------------------
# Documentation (mkdocs in documentation/)
# -------------------------------------------------------------------

# Clean and rebuild documentation (mkdocs + docs/)
docs_all: docs_clean docs_build

# Build mkdocs site into documentation/mkdocs/site
docs_build_mkdocs:
    cd "$DOCS_ROOT" && \
    mkdir -p mkdocs/docs && \
    rm -rf mkdocs/docs/generated mkdocs/site && \
    cp -r technical_reference_manual mkdocs/docs/technical_reference_manual && \
    python3 mkdocs/gen_docs.py && \
    cd mkdocs && mkdocs build

# Build docs/ tree from mkdocs output (gh-pages-ready)
docs_build: docs_build_mkdocs
    cd "$DOCS_ROOT" && \
    rm -rf docs && \
    mkdir -p docs && \
    cp -r mkdocs/site docs/mkdocs

# Build and serve docs at http://localhost:8000
docs_serve: docs_build
    cd "$DOCS_ROOT/docs" && python3 -m http.server 8000

# Publish docs to gh-pages branch
docs_publish_gh_pages:
    cd "$DOCS_ROOT" && bash publish_gh-pages.sh

# Publish docs (wrapper with reminder to review publish.env)
docs_publish: docs_publish_gh_pages
    @echo "Review documentation/publish.env before publishing."

# Watch docs and rebuild automatically on changes (needs inotify-tools)
docs_watch:
    cd "$DOCS_ROOT" && \
    while inotifywait -e modify -e create -e delete -r .; do \
        just docs_build; \
    done

# Remove generated docs and mkdocs build artifacts
docs_clean:
    cd "$DOCS_ROOT" && \
    rm -rf docs mkdocs/docs mkdocs/site technical_reference_manual/generated/

# Interactive spellcheck of technical_reference_manual via aspell container
docs_spellcheck: docs_clean
    cd "$DOCS_ROOT" && \
    docker build -f Dockerfile.aspell -t aspell . && \
    docker run -it --rm -u "{{uid}}:{{gid}}" -v "$PWD:/mnt" aspell \
      bash -lc 'find /mnt/technical_reference_manual -name "*.md" -exec aspell check --encoding=utf-8 --mode=markdown --home-dir=/mnt --personal=/mnt/.aspell.en.pws {} \;'

# Non-interactive spellcheck/lint of docs using aspell container
docs_lint: docs_clean
    cd "$DOCS_ROOT" && \
    docker build -f Dockerfile.aspell -t aspell . && \
    docker run -u "{{uid}}:{{gid}}" -v "$PWD:/mnt" aspell:latest python3 spellcheck.py
