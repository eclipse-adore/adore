ARG PROJECT?="sumo"

FROM ubuntu:22.04

ARG PROJECT

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    cmake \
    build-essential \
    fakeroot \
    sudo \
    software-properties-common \
    gnupg \
    wget \
    ca-certificates \
 && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /tmp/${PROJECT}
WORKDIR /tmp/${PROJECT}

COPY CMakeLists.txt .
COPY debian/postinst debian/postinst
RUN chmod +x debian/postinst

RUN mkdir build && cd build && \
    cmake .. && \
    cpack -G DEB

CMD ["bash", "-c", "ls -lh build/*.deb && dpkg-deb -I build/*.deb"]

