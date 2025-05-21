ARG PROJECT

FROM --platform=${TARGETPLATFORM:-linux/amd64} ubuntu:22.04 AS libopendrive_requirements_base

ARG PROJECT
ARG REQUIREMENTS_FILE="requirements.libOpenDRIVE.system"

RUN mkdir -p /tmp/libOpenDRIVE
WORKDIR /tmp/libOpenDRIVE
COPY ${REQUIREMENTS_FILE} /tmp/libOpenDRIVE

ENV DEBIAN_FRONTEND=noninteractive

RUN --mount=target=/var/lib/apt/lists,type=cache,sharing=locked \
    --mount=target=/var/cache/apt,type=cache,sharing=locked \
    apt-get update && \
    apt-get install --no-install-recommends -y \
        ca-certificates \
        checkinstall \
        build-essential \
        cmake \
        git \
        locales && \
    xargs apt-get install --no-install-recommends -y < ${REQUIREMENTS_FILE} && \
    rm -rf /var/lib/apt/lists/*


RUN echo "en_US.UTF-8 UTF-8" > /etc/locale.gen && \
    locale-gen
ENV LANG=en_US.UTF-8
ENV LANGUAGE=en_US:en
ENV LC_ALL=en_US.UTF-8

RUN mkdir -p /tmp/libOpenDRIVE
WORKDIR /tmp/libOpenDRIVE

COPY libOpenDRIVE /tmp/libOpenDRIVE/libOpenDRIVE
COPY packing.cmake /tmp/libOpenDRIVE/libOpenDRIVE/packing.cmake
COPY *.txt /tmp/libOpenDRIVE/

WORKDIR /tmp/libOpenDRIVE/libOpenDRIVE

RUN cat packing.cmake >> CMakeLists.txt

SHELL ["/bin/bash", "-c"]

RUN mkdir -p build
WORKDIR /tmp/libOpenDRIVE/libOpenDRIVE/build
RUN cmake .. \
    -DCMAKE_SYSTEM_NAME=Linux \
    -DCMAKE_C_COMPILER=/usr/bin/gcc \
    -DCMAKE_CXX_COMPILER=/usr/bin/g++ && \
    make -j"$(nproc)" && \
    make install

RUN cpack -G DEB && \
    find . -type f -name "*.deb" -exec mv {} . \;

RUN mv CMakeCache.txt CMakeCache.txt.build
