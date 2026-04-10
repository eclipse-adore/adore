# ADORe Embedded — Release

## Requirements

**Docker (recommended)**
- Docker Engine 24+ — [install guide](https://docs.docker.com/engine/install/)
- `x86_64` or `aarch64` host matching the image architecture in the filename

**Docker-free bundle**
- `podman` — [install guide](https://podman.io/docs/installation), **or**
- `util-linux` with `unshare`, `chroot`, and `mount` (standard on most Linux distributions)

## Unpack

The release is distributed as a `.tar.gz` archive. Extract it anywhere on the target system:

```bash
tar -xzf adore_embedded_<tag>.tar.gz
cd adore_embedded_<tag>
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

## Dev vs dist workspace

| | Dev (`shell_dev.sh`) | Dist (`shell_dist.sh`) |
|---|---|---|
| Mount | Live `ros2_workspace/` from host | Pre-built `ros2_workspace_dist/` baked into the image |
| ROS2 setup | Not sourced — run `source install/setup.bash` after building | Sourced automatically on shell entry |
| Use when | Actively modifying and rebuilding source | Running scenarios against a known-good build |

Use `shell_dev.sh` during development. Use `shell_dist.sh` to run scenarios against the shipped build without any host dependencies.

## Docker-free (bundle)

No Docker required. Uses `podman` if available, otherwise falls back to `unshare`/`chroot`:

```bash
./bundle_run.sh
./bundle_shell_dist.sh   # dist workspace shell
./bundle_shell_dev.sh    # dev workspace shell
```

## Rebuild ROS2 workspace

```bash
./shell_dev.sh      # enter dev shell
make build          # rebuild inside container
```

Or non-interactively:

```bash
./build_ros_workspace.sh
```

## Contents

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
| `*.tar.gz` | Docker image archive |
