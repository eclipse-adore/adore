# ADORe CLI

A containerized development environment for ROS2-based autonomous driving research and development.

## Overview

ADORe CLI provides a complete, reproducible development environment with ROS2, debugging tools, visualization capabilities, and cross-platform support. It automatically manages Docker containers and provides intelligent tag tracking to handle development workflow changes seamlessly. The system is highly extensible - simply drop requirements files anywhere in your project tree and ADORe CLI will automatically discover and install all dependencies during the build process.

## Quick Start

```bash
# Clone and initialize submodules
git submodule update --init --recursive

# Start the development environment
make cli

# Build from scratch (if needed)
make build

# Stop the environment
make stop
```

## Key Features

- **One-command setup**: `make cli` handles everything
- **Smart tag tracking**: Automatically detects environment changes and prompts for action
- **Cross-platform builds**: Support for ARM64 and x86_64 architectures  
- **Development tools**: Integrated plotting, debugging, and tracing capabilities
- **Hot reloading**: Automatically rebuilds when requirements change
- **Multiple display modes**: Native X11, headless, or window manager support
- **Auto-discovery**: Recursively finds and combines all requirements files

## Available Commands

| Command | Description |
|---------|-------------|
| `make cli` | Start or attach to development environment |
| `make build` | Build both core and runtime containers |
| `make clean` | Remove containers and build artifacts |
| `make run cmd="..."` | Execute command in container |
| `make stop` | Stop running containers |
| `make test` | Run CI tests |
| `make help` | Show all available make targets |

## Architecture

ADORe CLI uses a two-stage Docker build:

1. **Core Image** (`adore_cli_core`): Base ROS2 environment with system dependencies
2. **Runtime Image** (`adore_cli`): Extended environment with development tools and user packages

## Display Modes and Graphical Applications

ADORe CLI supports multiple display configurations for running graphical applications like RViz2, PlotJuggler, and custom visualization tools:

### Native Display Mode (Default)
Directly forwards X11 display to host system:
```bash
# Uses host display (default)
make cli
```
- **Pros**: Best performance, native look and feel
- **Cons**: Requires X11 server on host
- **Use case**: Local development with GUI applications

### Headless Mode
Runs without any display server for server/CI environments:
```bash
# Start in headless mode
DISPLAY_MODE=headless make cli
```
- **Pros**: Minimal resource usage, works anywhere
- **Cons**: No graphical applications
- **Use case**: CI/CD, remote servers, command-line only workflows

### Window Manager Mode
Provides isolated display environment:
```bash
# Start with window manager
DISPLAY_MODE=window_manager make cli
```
- **Pros**: Isolated from host display, consistent environment
- **Cons**: Additional overhead
- **Use case**: Reproducible GUI testing, multiple concurrent sessions

### Graphical Application Support

ADORe CLI includes pre-installed graphical tools:
- **RViz2**: 3D visualization for robot data
- **PlotJuggler**: Real-time plotting and data analysis
- **X11 apps**: xterm, xclock for testing display connectivity

### Testing Display Setup
```bash
# Inside ADORe CLI, test X11 forwarding
xclock

# Test ROS2 visualization
rviz2

# Launch PlotJuggler
ros2 run plotjuggler plotjuggler
```

### Troubleshooting Display Issues
```bash
# Check display environment
echo $DISPLAY

# Test basic X11 connectivity
xeyes

# For permission issues on Linux hosts
xhost +local:docker
```

## Automatic Requirements Discovery

ADORe CLI automatically discovers and combines requirements files from your entire project tree:

### Supported File Types
- **`*.system`**: APT/system packages (one per line)
- **`*.pip3`**: Python packages (one per line) 
- **`requirements.ppa`**: Ubuntu PPAs (ppa:repository/name format)

### How It Works
1. **Recursive Search**: Scans entire source directory tree for requirements files
2. **Smart Filtering**: Excludes `/ros_translator/*` paths and removes comments/empty lines
3. **Deduplication**: Combines and sorts all found dependencies
4. **Auto-Install**: Installs during container build process

### File Locations
Place requirements files anywhere in your project:
```
project/
├── requirements.system              # Root level
├── module_a/
│   └── requirements.module_a.pip3   # Module specific
└── drivers/
    ├── camera/
    │   └── camera_driver.system     # Deep nesting
    └── requirements.ppa             # PPAs
```

## Customization

### Adding System Packages
Create `*.system` files anywhere in your project:
```bash
# Example: my_module/requirements.system
ros-jazzy-nav2-bringup
gdb
htop
```

### Adding Python Packages  
Create `*.pip3` files anywhere in your project:
```bash
# Example: algorithms/requirements.pip3
numpy>=1.20.0
matplotlib
scipy
```

### Adding PPAs
Create `requirements.ppa` files anywhere in your project:
```bash
# Example: tools/requirements.ppa
ppa:deadsnakes/ppa
ppa:graphics-drivers/ppa
```

## Cross-Platform Development

Build for different architectures:
```bash
# ARM64
ARCH=arm64 make build

# x86_64 (default)
ARCH=x86_64 make build
```

Without specifying an arch the ADORe CLI will build for what ever target
platform it is running on. Cross compiling is only supported in ubuntu.

## Tag Memory System

ADORe CLI intelligently tracks container states:

- **Detects changes**: Warns when environment configuration changes
- **Offers choices**: Rebuild with new changes, reuse existing container, or abort
- **Preserves work**: Allows reconnection to existing containers
- **Auto-cleanup**: Clears history on rebuilds

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `ROS_DISTRO` | ROS2 distribution | `jazzy` |
| `ARCH` | Target architecture | `x86_64` |
| `SOURCE_DIRECTORY` | Host source directory | Current directory |
| `DISPLAY_MODE` | Display mode (native/headless/window_manager) | `native` |

## Requirements

- Docker 28+
- Make
- Git
- For cross-compilation: qemu-user-static, binfmt-support (auto installed in ubuntu if a cross compile is detected)

## Development Workflow

1. **Start environment**: `make cli`
2. **Develop**: Edit code in mounted source directory
3. **Add dependencies**: Create requirements files as needed anywhere in your project
4. **Rebuild**: `make build` automatically discovers and installs all requirements
5. **Test**: `make test` to run validation

## Included Tools

- **ROS2 Jazzy**: Complete ROS2 development stack
- **Visualization**: PlotJuggler, Foxglove Bridge, RViz2
- **Debugging**: GDB, GDBServer, network tools
- **Tracing**: ROS2 tracing tools and acceleration
- **Development**: Vim, Git, build tools, ccache

---

For detailed documentation and troubleshooting, run `help` inside the ADORe CLI environment.
