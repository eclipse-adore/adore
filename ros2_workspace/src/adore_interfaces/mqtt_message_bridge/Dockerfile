ARG ROS_DISTRO=jazzy
FROM ros:${ROS_DISTRO}-ros-base
ARG ROS_DISTRO=jazzy

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3-pip \
    python3-yaml \
    python3-numpy \
    python3-cryptography \
    mosquitto \
    mosquitto-clients \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

# Noble ships python3-paho-mqtt 1.6, which predates CallbackAPIVersion.VERSION2.
RUN pip3 install --no-cache-dir --break-system-packages 'paho-mqtt>=2.0.0'

WORKDIR /ws
COPY . /ws/src/mqtt_message_bridge/

ENV MQTT_BRIDGE_CERT_DIR=/ws/src/mqtt_message_bridge/certs

RUN . /opt/ros/${ROS_DISTRO}/setup.sh && \
    cd /ws && \
    colcon build --packages-select mqtt_message_bridge

COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh
ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["bridge"]
