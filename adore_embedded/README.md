# adore_embedded

This project builds a complete stand-alone deployment package for ADORe
with a versioned Docker image for the ADORe ROS2 workspace. The image bundles
all system, Python, and vendor dependencies needed to compile and run the 
workspace in a reproducible environment.

Each build is tagged with the current git commit and a hash of all dependency 
files, so the image tag changes only when the code or dependencies change.

The output package in `build/<tag>` can be copied to a new host and executed
immediately. The output package only requires docker to execute.

## Requirements

- Docker
- GNU Make

## Usage

```
make build    Build the image, compile the ROS2 workspace, and save to build/<tag>/
make start    Start the container with the workspace mounted
make stop     Stop and remove the container
make shell    Open a shell inside the running container
make clean    Remove the image, build output, and context
make help     Show available targets
```

The first `make build` produces a `build/<tag>/` directory containing the 
image archive, compiled workspace, and helper 
scripts (`load.sh`, `shell.sh`, `run.sh`, `stop.sh`) for use on machines 
without this repo.

## Configuration

Environment variables passed to the container are read from `container.env`. 
The ROS distro and target architecture can be overridden at build time:

```
make build ROS_DISTRO=humble ARCH=aarch64
```
