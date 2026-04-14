# syntax=docker/dockerfile:1
ARG ROS_DISTRO=jazzy
ARG OS_CODE_NAME=noble

FROM ros:${ROS_DISTRO}-ros-core-${OS_CODE_NAME} AS base

ARG ROS_DISTRO=jazzy
ARG ARCH
ARG SHORT_HASH
ARG REQUIREMENTS_HASH

ENV ROS_DISTRO=${ROS_DISTRO}

LABEL org.adore.image-type="embedded" \
      org.adore.arch="${ARCH}" \
      org.adore.commit="${SHORT_HASH}" \
      org.adore.requirements-hash="${REQUIREMENTS_HASH}"

RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt/lists,sharing=locked \
    rm -f /etc/apt/apt.conf.d/docker-clean && \
    apt-get update && \
    apt-get upgrade -y --no-install-recommends

RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt/lists,sharing=locked \
    apt-get install -y --no-install-recommends \
        build-essential \
        cmake \
        gettext-base \
        git \
        ccache \
        make \
        python3-pip \
        python3-colcon-common-extensions

COPY context /tmp/context

RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt/lists,sharing=locked \
    bash /tmp/context/install_requirements.sh

RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt/lists,sharing=locked \
    bash /tmp/context/install_packages.sh && \
    rm -rf /tmp/context

RUN git clone --recursive https://github.com/osqp/osqp.git /tmp/osqp && \
    cmake -S /tmp/osqp -B /tmp/osqp/build -G "Unix Makefiles" && \
    cmake --build /tmp/osqp/build -j$(nproc) && \
    cmake --install /tmp/osqp/build --prefix /usr/local && \
    ldconfig && \
    rm -rf /tmp/osqp

RUN echo "/usr/local/lib" >> /etc/ld.so.conf.d/local.conf && ldconfig

# ── Workspace build stage ──────────────────────────────────────────────────────
# ros2_workspace is supplied as an external BuildKit build context:
#   docker build --build-context ros2_workspace=../ros2_workspace ...
FROM base AS workspace-builder

COPY --from=ros2_workspace src                  /ros2_workspace_dist/src
COPY --from=ros2_workspace Makefile             /ros2_workspace_dist/Makefile
COPY --from=ros2_workspace colcon_defaults.yaml /ros2_workspace_dist/colcon_defaults.yaml

RUN --mount=type=cache,target=/root/.ccache,sharing=locked \
    . /opt/ros/${ROS_DISTRO}/setup.sh && \
    cd /ros2_workspace_dist && \
    make build && \
    rm -rf /ros2_workspace_dist/log

# ── Runtime image ──────────────────────────────────────────────────────────────
FROM base AS runtime

RUN echo "source /opt/ros/${ROS_DISTRO}/setup.bash" >> /etc/bash.bashrc && \
    echo "source /ros2_workspace_dist/install/setup.bash" >> /etc/bash.bashrc && \
    echo "source /ros2_workspace/install/setup.bash 2>/dev/null || true" >> /etc/bash.bashrc

RUN mkdir -p /home/user && chmod 1777 /home/user
ENV HOME=/home/user

# Pre-built workspace baked into the image; volume-mount /ros2_workspace at
# runtime to override with a live workspace for development.
COPY --from=workspace-builder /ros2_workspace_dist /ros2_workspace_dist
# adore_scenarios supplied via: --build-context adore_scenarios=../adore_scenarios
COPY --from=adore_scenarios . /ros2_workspace_dist/adore_scenarios
COPY context                  /ros2_workspace_dist/context

WORKDIR /ros2_workspace_dist
