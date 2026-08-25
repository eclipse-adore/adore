ARG ROS_DISTRO=jazzy
ARG OS_CODE_NAME=noble
FROM ros:${ROS_DISTRO}-ros-core-${OS_CODE_NAME} AS base

ARG ROS_DISTRO=jazzy
ENV ROS_DISTRO=${ROS_DISTRO}
ENV DEBIAN_FRONTEND=noninteractive

COPY requirements.system /tmp/requirements.system
RUN apt-get update && apt-get install -y \
    python3-pip \
    python3-colcon-common-extensions \
    $(grep -v '^\s*#' /tmp/requirements.system | tr '\n' ' ') \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /ros2_ws/src/weather_service_interface
COPY . .

RUN pip3 install --break-system-packages -r requirements.pip3

WORKDIR /ros2_ws
RUN . /opt/ros/${ROS_DISTRO}/setup.sh && \
    colcon build --packages-select weather_service_interface

RUN printf '#!/usr/bin/env bash\nset -e\nsource /opt/ros/${ROS_DISTRO}/setup.bash\nsource /ros2_ws/install/setup.bash\nexec "$@"\n' > /entrypoint.sh && \
    chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
