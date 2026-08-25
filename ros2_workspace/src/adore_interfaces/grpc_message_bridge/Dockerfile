ARG ROS_DISTRO=jazzy
FROM ros:${ROS_DISTRO}-ros-base

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3-pip \
    python3-grpcio \
    python3-yaml \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install --no-cache-dir --break-system-packages grpcio-tools protobuf

WORKDIR /ws
COPY . /ws/src/grpc_message_bridge/

ENV PYTHONPATH=/ws/src/grpc_message_bridge/proto/generated

RUN . /opt/ros/${ROS_DISTRO}/setup.sh && \
    cd /ws && \
    colcon build --packages-select grpc_message_bridge

COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh
ENTRYPOINT ["/docker-entrypoint.sh"]
