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

#RUN ln -sf /usr/bin/python3.12 /usr/bin/python3.10 && \
#    ln -sf /usr/include/python3.12 /usr/include/python3.10

RUN ARCH=$(uname -m) && \
    case "$ARCH" in \
        x86_64)   ln -sf /usr/lib/x86_64-linux-gnu/libgdal.so /usr/lib/libgdal.so ;; \
        aarch64)  ln -sf /usr/lib/aarch64-linux-gnu/libgdal.so /usr/lib/libgdal.so ;; \
        *)        echo "Unsupported architecture: $ARCH"; exit 1 ;; \
    esac

RUN export SUMO_HOME="$PWD" && \
   python_arch=$(case "$(uname -m)" in x86_64) echo "x86_64-linux-gnu" ;; aarch64) echo "aarch64-linux-gnu" ;; *) echo "$(uname -m)-linux-gnu" ;; esac) && \
   python_version=$(python3 --version | sed 's/Python \([0-9]\+\.[0-9]\+\).*/\1/') && \
   cmake -B build . \
       -DPython3_EXECUTABLE=$(which python3) \
       -DPython3_INCLUDE_DIR=/usr/include/python${python_version} \
       -DPython3_LIBRARY=/usr/lib/${python_arch}/libpython${python_version}.so && \
   cmake --build build -j$(($(nproc) > 1 ? $(nproc) : 1))
