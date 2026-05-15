FROM ros:humble-ros-core-jammy

ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8

RUN apt-get update && apt-get install -y --no-install-recommends \
    ros-humble-rmw-zenoh-cpp \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /ros2_ws

ENTRYPOINT ["/bin/bash", "-c", "source /opt/ros/humble/setup.bash && exec \"$@\"", "--"]
CMD ["bash"]
