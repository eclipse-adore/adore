<!--
********************************************************************************
* Copyright (C) 2017-2020 German Aerospace Center (DLR). 
* Eclipse ADORe, Automated Driving Open Research https://eclipse.org/adore
*
* This program and the accompanying materials are made available under the 
* terms of the Eclipse Public License 2.0 which is available at
* http://www.eclipse.org/legal/epl-2.0.
*
* SPDX-License-Identifier: EPL-2.0 
*
* Contributors: 
********************************************************************************
-->
# ADORe Docker-Based Development Environment

## Overview

The ADORe project ships a Docker-based development environment so you can:

* Develop against a **reproducible ROS 2 (Jazzy) stack**.
* Keep your host system relatively clean.
* Share the same setup across contributors and CI.
* Avoid permission issues by matching the container user to your host user.
* Keep your shell history and workspace state **across container restarts**.

This document explains how it is structured and how to use it day-to-day.

---

## Components

### Docker images

There are three main images, all configured via `.docker/scripts/common.sh`:

* **Base image** – `adore_base:<tag>` / `adore_base:latest`

  * Built from `.docker/base/Dockerfile`.
  * Contains OS, ROS 2 Jazzy and base APT dependencies.
  * No user mapping or developer tooling.

* **Dev image** – `adore_dev:<tag>` / `adore_dev:latest`

  * Defined in `.docker/dev/Dockerfile`.
  * `FROM adore_base:latest`.
  * Installs additional developer packages from `.docker/dev/apt.dev.txt`, including e.g.:

    * Shell & terminal tools: `zsh`, `fzf`, `zsh-syntax-highlighting`, `zsh-autosuggestions`, `htop`, `tree`, `bat`, `ripgrep`, `gdb`.
    * ROS tools: `ros-jazzy-rqt`, `ros-jazzy-rqt-common-plugins`, `ros-jazzy-foxglove-bridge`, `ros-jazzy-ros2trace`, `ros-jazzy-tracetools-analysis`.
    * Tracing & debugging: `babeltrace`, `lttng-modules-dkms`.
    * X11 utilities & libraries: `x11-apps`, `libx11-6`, `libxext6`, `libxrender1`, `libxtst6`, `libxi6`, `libgl1`, `mesa-utils`, `x11-utils`.
    * Web & misc: `python3-flask`, `python3-flask-cors`, `jq`. 
  * Installs the **Helix editor** (`hx`) and sets `HELIX_RUNTIME`.
  * Installs **Oh My Zsh** (non-interactive) and configures zsh as the default shell.
  * Configures **ccache** and a large, persistent zsh history.
  * Creates or renames a non-root user that matches your host UID/GID.

* **CI image** – `adore_ci:<tag>` / `adore_ci:latest`

  * Built from `.docker/ci/Dockerfile`.
  * Used by CI and docs helpers (e.g. `just docs`, `just ci`).
  * Not required for basic development, but available via `Justfile` recipes.

Each image is tagged with both `:latest` and a content-addressed tag based on:

```bash
IMAGE_TAG = "${GIT_HASH}-${ARCH}"
```

where `GIT_HASH` is the short git commit hash of the repo, and `ARCH` is the machine architecture.

---

## Scripts and helpers

### `.docker/dev/Dockerfile`

Key behavior of the dev image:

* **Apt dependencies**

  * Copies `.docker/dev/apt.dev.txt` into the image and installs everything via `apt-get`.
* **Helix**

  * Downloads a specific Helix release, unpacks it into `/opt/helix`.
  * Adds `/usr/local/bin/hx` symlink.
  * Sets `HELIX_RUNTIME=/opt/helix/runtime` in `/etc/profile`.
* **User mapping**

  * Build args: `USERNAME` (default `developer`), `USER_UID` (default 2001), `USER_GID` (default 2001).
  * At build time:

    * If a user already exists with `USER_UID`, it is **renamed** to `${USERNAME}` and its home directory moved to `/home/${USERNAME}` while the group is renamed accordingly.
    * Otherwise a new user `${USERNAME}` is created with that UID/GID and `/usr/bin/zsh` as the shell.
  * The `USER` instruction switches to `${USERNAME}` for the rest of the Dockerfile and at runtime.
* **Workspace & ccache**

  * Sets `WORKSPACE="/home/${USERNAME}/adore"` and `WORKDIR ${WORKSPACE}`.
  * Configures ccache via env vars:

    * `CCACHE_DIR="${WORKSPACE}/.cache/ccache"`
    * `CC="/usr/lib/ccache/gcc"`
    * `CXX="/usr/lib/ccache/g++"`
* **Zsh configuration**

  * Appends to `${USERNAME}`’s `.zshrc`:

    * `HISTFILE=~/adore/.zsh_history`
    * `HISTSIZE=100000`, `SAVEHIST=100000`
    * `setopt HIST_IGNORE_DUPS`, `HIST_REDUCE_BLANKS`, `SHARE_HISTORY`, `INC_APPEND_HISTORY`
  * Ensures the workspace directory and history file exist and are owned by `${USERNAME}`.
* **ROS & overlay auto-sourcing**

  * Appends a block to `.zshrc` that:

    * Sources `/opt/ros/${ROS_DISTRO:-jazzy}/setup.zsh` if it exists.
    * Sources the local colcon workspace overlay, preferring:

      * `$HOME/adore/install/local_setup.zsh`
      * then `$HOME/adore/install/setup.zsh`.
* **Default command**

  * The container entrypoint is a login zsh shell:

    ```dockerfile
    CMD ["/usr/bin/zsh", "-l"]
    ```

---

### `.docker/scripts/build_dev.sh`

Builds the **base** and **dev** images on the host:

1. Loads `common.sh` and asserts it is running on the host (via `require_host`).

2. Switches to `$WORKSPACE_ROOT`.

3. If `adore_base:latest` does not exist, builds it:

   ```bash
   docker build \
     -f "${DOCKER_BASE_DOCKERFILE}" \
     -t "${DOCKER_BASE_IMAGE_LATEST}" \
     -t "${DOCKER_BASE_IMAGE_TAGGED}" \
     .
   ```

4. Always builds the dev image:

   ```bash
   docker build \
     -f "${DOCKER_DEV_DOCKERFILE}" \
     --build-arg USER_UID="${USER_UID}" \
     --build-arg USER_GID="${USER_GID}" \
     --build-arg USERNAME="${USER_NAME}" \
     -t "${DOCKER_DEV_IMAGE_LATEST}" \
     -t "${DOCKER_DEV_IMAGE_TAGGED}" \
     .
   ```

The build args ensure the dev image’s user matches your host user, avoiding permission issues on the bind-mounted workspace.

---

### `.docker/scripts/run_dev.sh`

Starts or attaches to the dev container (host-side script):

1. Loads `common.sh` and enforces host execution (`require_host`).

2. Ensures the dev image exists:

   * If `adore_dev:latest` is missing, calls `build_dev.sh`.

3. Sets `IMAGE="${DOCKER_DEV_IMAGE_LATEST}"` and `CONTAINER_NAME="${DOCKER_CONTAINER_NAME}"`.

4. If a container with that name is **running**:

   * Clears the screen, prints `dev_greeting`, and runs:

     ```bash
     docker exec -it \
       -w "/home/${USER_NAME}/adore/" \
       -e HISTFILE="/home/${USER_NAME}/.zsh_history" \
       -e HISTSIZE=100000 \
       -e SAVEHIST=100000 \
       "${CONTAINER_NAME}" \
       zsh
     ```

   * Then exits (you’re now attached to the existing container).

5. If a container with that name exists but is **stopped**, it is removed.

6. Ensures host-side zsh history file exists:

   ```bash
   HOST_ZSH_HISTORY="${WORKSPACE_ROOT}/.zsh_history"
   touch "${HOST_ZSH_HISTORY}"  # if missing
   ```

7. Starts a **fresh** dev container:

   ```bash
   docker run --rm -it \
     --name "${CONTAINER_NAME}" \
     --network host \
     -e DISPLAY \
     -e QT_X11_NO_MITSHM=1 \
     -v /tmp/.X11-unix:/tmp/.X11-unix:rw \
     -v "${WORKSPACE_ROOT}:/home/${USER_NAME}/adore" \
     -v "${HOST_ZSH_HISTORY}:/home/${USER_NAME}/.zsh_history" \
     -w "/home/${USER_NAME}/adore/" \
     -e ROS_DISTRO="${ROS_DISTRO}" \
     -e HISTFILE="/home/${USER_NAME}/.zsh_history" \
     -e HISTSIZE=100000 \
     -e SAVEHIST=100000 \
     "${IMAGE}"
   ```

8. Before you get the shell prompt, the script clears the terminal and prints the `dev_greeting` banner.

Key points:

* **Host networking** (`--network host`) simplifies ROS 2 discovery and interaction with host services.
* **X11 support** is set up via the `/tmp/.X11-unix` bind mount and `DISPLAY`/`QT_X11_NO_MITSHM`.
* Shell history is **persisted on the host** (`.zsh_history` in the repo) and reused across containers.

---



## Justfile integration

The `Justfile` in the repo root ties all of this together.

Important recipes related to the dev environment:

* **Entry points**

  * `just` or `just help` – list all available recipes.
  * `just dev` – run the dev container.
* **Docker images**

  * `just build_dev` – build base + dev images (host).
  * `just clean_images` – remove local ADORe images.
  * `just save` / `just load` – save/load dev/CI images as tarballs.
* **Workspace cleanup**

  * `just clean_ws` – delete `{build,install,log}`.
  * `just clean` – `clean_images` + `clean_ws`.
  * `just clean_build` – clean the workspace and then build.
* **Colcon builds & tests** (host or inside the dev container)

  * `just build` – build the workspace.
  * `just test_ws` – run `colcon test` (skipping vendor packages) + `colcon test-result`.
  * `just build_scenarios`, `just build_nodes`, etc. – targeted builds for subsets of packages.
* **Tools & GUI**

  * `just gui` – run the ADORe scenario launcher.
  * `just edit_roads` – road network editor.
  * `just lichtblick` – Lichtblick visualization wrapper.
* **Docs & CI**

  * `just docs` – build documentation inside the CI image.
  * `just ci` – run a CI-like test/docs pipeline locally.

You can run these either **on the host** (if you have ROS and dependencies installed) or **inside the dev container** (recommended, since that environment is controlled and consistent).

---

## Container layout and runtime environment

Once you’re inside the dev container via `just dev` or `.docker/scripts/run_dev.sh`:

* Working directory: `/home/<user>/adore` (the mounted repo).
* Colcon workspace: `/home/<user>/adore`.
* Sources: Top-level packages directories (`adore_nodes` etc).
* Default shell: `zsh` with Oh My Zsh and custom history options.
* Editor: `hx` (Helix) is available.
* ROS:

  * `/opt/ros/$ROS_DISTRO/setup.zsh` is sourced automatically.
  * If you have built the workspace, the overlay under `install` is also sourced automatically by `.zshrc`.

All ROS tools from `apt.dev.txt` are ready to use: `rqt`, `ros2trace`, `foxglove-bridge`, etc.

---

## Typical workflow

1. **Clone the repo** (on your host machine):

   ```bash
   git clone <ado-repo> adore
   cd adore
   ```

2. **Start the dev container**:

   ```bash
   just dev
   ```

   This will:

   * Build the base/dev images if needed.
   * Start the container or attach to it if already running.
   * Drop you into a login zsh shell inside `adore_dev`.

3. **Build the workspace** (inside the container):

   ```bash
   cd ~/adore
   colcon build
   ```

   Or:

   ```bash
   just build
   ```

4. **Run tests**:

   ```bash
   just test_ws
   ```

5. **Run tools and GUIs**:

   ```bash
   # Scenario launcher
   just gui

   # Road editor
   just edit_roads

   # Visualization
   just lichtblick
   ```

6. **Stop / restart later**

   * Simply exit the shell to stop the container (because it was started with `--rm`).
   * Next time, run `just dev` again; your workspace state and shell history are preserved.

---

## Summary

The ADORe Docker development environment provides:

* A consistent ROS 2 Jazzy-based stack with all necessary tools.
* A user inside the container that matches your host user, avoiding permissions pain.
* A colcon workspace layout centered on the project root.
* Simple host-side entrypoints (`just dev`, `.docker/scripts/run_dev.sh`) to start or attach to a ready-to-use dev shell.
* Persistent shell history and a curated CLI experience tuned for day-to-day ADORe development.