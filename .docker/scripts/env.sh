#!/usr/bin/env bash
# Environment helpers shared by all ADORe scripts.

# NOTE: Do *not* set -euo pipefail here; the parent script does that.

# Detect whether we're running inside a Docker container.
is_in_docker() {
  if [[ -f "/.dockerenv" ]]; then
    return 0
  fi

  if grep -qiE '(docker|lxc|containerd)' /proc/1/cgroup 2>/dev/null; then
    return 0
  fi

  case "${CI:-}" in
    true|1|github_actions)
      # Treat CI as "in Docker" for our purposes.
      return 0
      ;;
  esac

  return 1
}

# Ensure a script is executed on the host (outside Docker).
require_host() {
  if is_in_docker; then
    echo "ERROR: This script is intended to be run on the HOST (outside Docker)." >&2
    if [[ $# -gt 0 ]]; then
      printf '%s\n' "$*" >&2
    fi
    exit 1
  fi
}

# Ensure a script is executed *inside* a Docker container.
require_docker() {
  if ! is_in_docker; then
    echo "ERROR: This script is intended to be run INSIDE a Docker container." >&2
    if [[ $# -gt 0 ]]; then
      printf '%s\n' "$*" >&2
    fi
    exit 1
  fi
}
