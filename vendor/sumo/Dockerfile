ARG PROJECT="sumo"

FROM ubuntu:24.04 AS sumo_builder

ARG PROJECT
ARG REQUIREMENTS_FILE="requirements.${PROJECT}.system"


WORKDIR /tmp/${PROJECT}
COPY ${REQUIREMENTS_FILE} /tmp/${PROJECT}

RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive xargs apt-get install --no-install-recommends -y < ${REQUIREMENTS_FILE} && \                                     
    rm -rf /var/lib/apt/lists/*

RUN mkdir -p /tmp/${PROJECT}
COPY ${PROJECT} /tmp/${PROJECT}

WORKDIR /tmp/${PROJECT}

RUN ln -s /usr/bin/python3.12 /usr/bin/python3.10
RUN ln -s /usr/include/python3.12 /usr/include/python3.10
RUN ln -s /usr/lib/x86_64-linux-gnu/libgdal.so /usr/lib/libgdal.so

RUN export SUMO_HOME="$PWD" && \
    cmake -B build . \
        -DPython3_EXECUTABLE=/usr/bin/python3.12 \
        -DPython3_INCLUDE_DIR=/usr/include/python3.12 \
        -DPython3_LIBRARY=/usr/lib/x86_64-linux-gnu/libpython3.12.so && \
    cmake --build build -j$(nproc)
