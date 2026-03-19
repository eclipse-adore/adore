ARG ROS_DISTRO=jazzy
ARG OS_CODE_NAME=noble
FROM ros:${ROS_DISTRO}-ros-core-${OS_CODE_NAME}

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
    apt-get update

RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt/lists,sharing=locked \
    apt-get install -y --no-install-recommends \
        build-essential \
        cmake \
        gettext-base \
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

RUN echo "source /opt/ros/${ROS_DISTRO}/setup.bash" >> /etc/bash.bashrc

RUN mkdir -p /home/user && chmod 1777 /home/user
ENV HOME=/home/user

WORKDIR /ros2_workspace
