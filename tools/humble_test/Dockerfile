FROM ros:humble-ros-core-jammy

ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8

RUN apt-get update && apt-get install -y --no-install-recommends \
    ros-humble-rmw-zenoh-cpp \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /ros2_ws

COPY ./entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENV ROS_DOMAIN_ID=62

ENTRYPOINT ["/entrypoint.sh"]
