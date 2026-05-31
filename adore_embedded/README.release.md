# ADORe Embedded — Release

## Requirements

**Docker (recommended)**
- Docker Engine 24+ — [install guide](https://docs.docker.com/engine/install/)
- `x86_64` or `aarch64` host matching the image architecture in the filename
- GNU Make

**Docker-free bundle**
- `podman` — [install guide](https://podman.io/docs/installation), **or**
- `util-linux` with `unshare`, `chroot`, and `mount` (standard on most Linux distributions)
- Lichtblick visualisation in the bundle requires `podman`

## Fetch

https://github.com/eclipse-adore/adore/releases/

Release: [<release_url>](<release_url>)

**Docker image**

```bash
# x86_64
curl -L -o <filename_x86_64> https://github.com/eclipse-adore/adore/releases/download/<release_tag>/<filename_x86_64>
wget https://github.com/eclipse-adore/adore/releases/download/<release_tag>/<filename_x86_64>

# aarch64
curl -L -o <filename_aarch64> https://github.com/eclipse-adore/adore/releases/download/<release_tag>/<filename_aarch64>
wget https://github.com/eclipse-adore/adore/releases/download/<release_tag>/<filename_aarch64>
```

**Docker-free bundle**

```bash
# x86_64
curl -L -o <filename_x86_64_bundle> https://github.com/eclipse-adore/adore/releases/download/<release_tag>/<filename_x86_64_bundle>
wget https://github.com/eclipse-adore/adore/releases/download/<release_tag>/<filename_x86_64_bundle>

# aarch64
curl -L -o <filename_aarch64_bundle> https://github.com/eclipse-adore/adore/releases/download/<release_tag>/<filename_aarch64_bundle>
wget https://github.com/eclipse-adore/adore/releases/download/<release_tag>/<filename_aarch64_bundle>
```

## Unpack

```bash
# x86_64
tar -xzf <filename_x86_64>
cd <dirname_x86_64>

# aarch64
tar -xzf <filename_aarch64>
cd <dirname_aarch64>
```

The image archive (`*.tar.gz`) inside the directory is loaded separately on first run — no manual extraction needed.

## Quick start

```bash
./load.sh              # import Docker image (first run only)
./start.sh             # start container
./start_lichtblick.sh  # start Lichtblick visualiser (optional)
./shell_dist.sh        # attach to pre-built workspace
./stop_lichtblick.sh   # stop visualiser
./stop.sh              # stop container
```

## Running a scenario

`shell_dist.sh` drops directly into the simulation scenarios directory with the workspace pre-sourced.

```bash
./shell_dist.sh
```

Inside the shell, launch any scenario by name:

```bash
ros2 launch simulation_test.launch.py
```

Other available scenarios in the same directory:

```bash
ros2 launch template.launch.py
ros2 launch dlr_campus.launch.py
ros2 launch saad_maad.launch.py
```

## Visualizing with Lichtblick

Lichtblick connects to the running scenario over rosbridge (WebSocket on port 9090) and renders a pre-configured layout shipped with the release.

**1. Start Lichtblick** (in a separate terminal, before or after launching a scenario):

```bash
./start_lichtblick.sh
```

**2. Launch a scenario** (in another terminal):

```bash
./shell_dist.sh
ros2 launch simulation_test.launch.py
```

**3. Open Lichtblick** in a Chromium-based browser:

```
http://localhost:8080/?ds=rosbridge-websocket&ds.url=ws://localhost:9090
```

The default layout loads automatically. To load the shipped layout explicitly, open it from `ros2_workspace_dist/context/` inside the container, or from the `adore_scenarios/assets/lichtblick_layouts/Default.json` path in the release directory.

> **Note:** Lichtblick requires a Chromium-based browser (Chrome, Chromium, Edge). Firefox is not supported.

**4. Stop when done:**

```bash
./stop_lichtblick.sh
./stop.sh
```

## Dev vs dist workspace

| | Dev (`shell_dev.sh`) | Dist (`shell_dist.sh`) |
|---|---|---|
| Mount | Live `ros2_workspace/` from host | Pre-built `ros2_workspace_dist/` baked into the image |
| ROS2 setup | Not sourced — run `source install/setup.bash` after building | Sourced automatically on shell entry |
| Use when | Actively modifying and rebuilding source | Running scenarios against a known-good build |

Use `shell_dev.sh` during development. Use `shell_dist.sh` to run scenarios against the shipped build without any host dependencies.

## Docker-free bundle

No Docker required. The bundle ships a complete Linux rootfs extracted from the Docker image alongside the pre-built ROS2 workspace and the Lichtblick image archive.

### How it works

`start.sh` uses `podman` if available, otherwise falls back to `unshare`/`chroot` from `util-linux`. Both paths mount the `ros2_workspace_dist/` directory from the bundle into the rootfs at runtime, so scenarios always run against the shipped build without copying it into the container.

The `unshare` path creates an unprivileged user namespace with a private mount and PID namespace, then calls `chroot` into the rootfs. No root access is required with either backend.

Lichtblick in the bundle requires `podman`. The Lichtblick container image is included in the bundle as `lichtblick/<archive>.tar.gz` and is imported into podman on first use.

### Unpack

```bash
tar -xzf <filename_bundle>
cd <dirname_bundle>
```

### Workflow

```bash
./shell_dist.sh          # enter the dist workspace shell
./shell_dev.sh           # enter the dev workspace shell
./stop.sh                # remove the imported podman image (podman only; no-op for unshare)
./start_lichtblick.sh    # start the Lichtblick visualiser (requires podman)
./stop_lichtblick.sh     # stop the Lichtblick visualiser
```

### Running a scenario (bundle)

Open two terminals in the bundle directory.

**Terminal 1 — start the environment and launch a scenario:**

```bash
./shell_dist.sh
ros2 launch simulation_test.launch.py
```

**Terminal 2 — start Lichtblick:**

```bash
./start_lichtblick.sh
```

Then open in a Chromium-based browser:

```
http://localhost:8080/?ds=rosbridge-websocket&ds.url=ws://localhost:9090
```

**When done:**

```bash
./stop_lichtblick.sh
./stop.sh
```

`stop.sh` removes the imported podman image (`adore_bundle_<ros_distro>`). Re-running `start.sh` or any shell script will re-import it from the rootfs directory on the next invocation. When using the `unshare` backend, `stop.sh` prints a notice and exits cleanly — there is no persistent state to remove.

### Backend selection

| Backend | Selected when | Persistent state |
|---|---|---|
| `podman` | `podman` is on `PATH` | Podman image `adore_bundle_<ros_distro>` imported on first run; removed by `stop.sh` |
| `unshare`/`chroot` | `podman` not found | None — namespace torn down when the shell exits |

### Bundle contents

| Path | Description |
|---|---|
| `rootfs/` | Complete Linux rootfs with all ROS2 and ADORe dependencies |
| `ros2_workspace_dist/` | Pre-built ROS2 workspace mounted into the rootfs at runtime |
| `lichtblick/<archive>.tar.gz` | Lichtblick container image archive, imported into podman on first use |
| `bundle.env` | `ROS_DISTRO` and `DOCKER_PLATFORM` consumed by the bundle scripts |
| `lichtblick.env` | `LICHTBLICK_IMAGE` and `LICHTBLICK_ARCHIVE_NAME` consumed by `start_lichtblick.sh` |
| `container.env` | Runtime environment variables passed into the environment |
| `start.sh` | Start an interactive session via podman or unshare/chroot |
| `stop.sh` | Remove the imported podman image; no-op for unshare |
| `shell_dist.sh` | Shell into the pre-built dist workspace |
| `shell_dev.sh` | Shell into the dev workspace |
| `start_lichtblick.sh` | Start Lichtblick via podman (loads archive on first use) |
| `stop_lichtblick.sh` | Stop the Lichtblick podman container |
| `.bundle_inner.sh` | Internal helper — mounts filesystems and execs into the chroot (not called directly) |
| `README.md` | This file |

## Rebuild ROS2 workspace

```bash
./shell_dev.sh      # enter dev shell
make build          # rebuild inside container
```

Or non-interactively:

```bash
./build_ros_workspace.sh
```

## Contents (Docker release)

| Path | Description |
|---|---|
| `adore.env` | Image name, tag, and container configuration |
| `container.env` | Runtime environment variables passed into the container |
| `load.sh` | Load the image archive into Docker |
| `start.sh` | Start the container detached |
| `stop.sh` | Stop and remove the container |
| `shell_dev.sh` | Interactive shell — live source workspace |
| `shell_dist.sh` | Interactive shell — pre-built distribution workspace |
| `build_ros_workspace.sh` | Rebuild the ROS2 workspace inside the container |
| `start_lichtblick.sh` / `stop_lichtblick.sh` | Lichtblick visualiser |
| `bundle_run.sh` | Run without Docker via podman or `unshare` |
| `bundle_shell_dev.sh` / `bundle_shell_dist.sh` | Shells for the Docker-free bundle |
| `ros2_workspace_dist/` | Pre-built ROS2 workspace |
| `lichtblick/` | Lichtblick image archive and supporting files |
| `*.tar.gz` | Docker image archive |
