ARG PROJECT

FROM debian:stable-slim AS libopendrive_requirements_base

ARG PROJECT
ARG REQUIREMENTS_FILE="requirements.libOpenDRIVE.system"

RUN mkdir -p /tmp/libOpenDRIVE
WORKDIR /tmp/libOpenDRIVE
COPY ${REQUIREMENTS_FILE} /tmp/libOpenDRIVE

ENV DEBIAN_FRONTEND=noninteractive

ENV DEBIAN_FRONTEND=noninteractive
RUN --mount=target=/var/lib/apt/lists,type=cache,sharing=locked \
    --mount=target=/var/cache/apt,type=cache,sharing=locked \
    apt-get update && \
    apt-get install --no-install-recommends -y checkinstall && \
    xargs apt-get install --no-install-recommends -y < ${REQUIREMENTS_FILE} && \
    rm -rf /var/lib/apt/lists/*

# Install build tools, dependencies, and UTF-8 locale
RUN echo "en_US.UTF-8 UTF-8" > /etc/locale.gen && locale-gen

ENV LANG=en_US.UTF-8
ENV LANGUAGE=en_US:en
ENV LC_ALL=en_US.UTF-8

COPY libOpenDRIVE /tmp/libOpenDRIVE/libOpenDRIVE
COPY packing.cmake /tmp/libOpenDRIVE/libOpenDRIVE/packing.cmake

WORKDIR /tmp/libOpenDRIVE
COPY *.txt .

ARG PROJECT
WORKDIR /tmp/libOpenDRIVE/libOpenDRIVE
RUN mkdir -p build 
SHELL ["/bin/bash", "-c"]
WORKDIR /tmp/libOpenDRIVE/libOpenDRIVE/build

# Configure the build with dynamic CPack injection
RUN cat ../packing.cmake >> ../CMakeLists.txt && \
    cmake ..
RUN make -j $(nproc) && make install
RUN cpack -G DEB && find . -type f -name "*.deb" ! -path "./*.deb" -exec mv {} . \;
RUN cd /tmp/libOpenDRIVE/libOpenDRIVE/build && \
    rm -rf install && \
    ln -s devel install && \
    mv CMakeCache.txt CMakeCache.txt.build


