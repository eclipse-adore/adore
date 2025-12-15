# .docker/base/Dockerfile
FROM ros:jazzy-ros-base

# Locale
ENV LANG=C.UTF-8 \
    LC_ALL=C.UTF-8

# Core APT dependencies (shared by dev & CI)
COPY .docker/base/apt.base.txt /tmp/apt.base.txt

RUN apt-get update && \
    xargs -r -a /tmp/apt.base.txt apt-get install -y && \
    rm -rf /var/lib/apt/lists/* /tmp/*
