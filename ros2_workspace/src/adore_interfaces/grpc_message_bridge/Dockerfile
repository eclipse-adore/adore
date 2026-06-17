ARG ROS_DISTRO=jazzy
ARG OS_CODE_NAME=noble
FROM ros:${ROS_DISTRO}-ros-core-${OS_CODE_NAME} AS base
ARG ROS_DISTRO=jazzy
ENV ROS_DISTRO=${ROS_DISTRO}
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3-pip \
    python3-colcon-common-extensions \
    ros-${ROS_DISTRO}-rosidl-runtime-py \
    ros-${ROS_DISTRO}-std-msgs \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /ros2_ws/src/grpc_message_bridge

COPY . .

RUN pip3 install --no-cache-dir --break-system-packages -r requirements.pip3

WORKDIR /ros2_ws

RUN . /opt/ros/${ROS_DISTRO}/setup.sh && \
    colcon build --packages-select grpc_message_bridge --symlink-install

ENV RMW_IMPLEMENTATION=rmw_fastrtps_cpp

COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

ENTRYPOINT ["/docker-entrypoint.sh"]
