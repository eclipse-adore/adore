#!/bin/bash
set -e

# === CONFIGURATION ===
LICHTBLICK_IMAGE="ghcr.io/lichtblick-suite/lichtblick:latest"
HOST_PORT=8080
CONTAINER_PORT=8080

# === Resolve directory of this script ===
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
MODELS_DIR="${SCRIPT_DIR}/../adore_scenarios/assets/"

# === Check if script is running inside Docker ===
is_inside_docker() {
    grep -qE '/docker/|/lxc/' /proc/1/cgroup 2>/dev/null || [ -f /.dockerenv ]
}

if is_inside_docker; then
    echo "🚫 You are running this script inside a Docker container."
    echo "💡 Please run it from your host terminal, not from inside container"
    exit 1
fi

# === Check if model directory exists ===
if [ ! -d "$MODELS_DIR" ]; then
    echo "❌ Error: Model directory '$MODELS_DIR' does not exist."
    exit 1
fi

echo "🚀 Starting Lichtblick in Docker..."
echo "🌐 Open http://localhost:${HOST_PORT} in Chrome."
echo "📦 Mounting 3D models from: $MODELS_DIR"
echo "🛑 Press Ctrl+C to stop the server."

# === Run Lichtblick container with 3D model mount ===
docker run --rm \
    -p "${HOST_PORT}:${CONTAINER_PORT}" \
    -v "${MODELS_DIR}:/src/assets" \
    "${LICHTBLICK_IMAGE}"

