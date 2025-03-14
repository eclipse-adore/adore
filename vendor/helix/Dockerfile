
ARG URL

FROM debian:stable-slim

ARG URL

WORKDIR /helix

RUN apt-get update && apt-get install -y \
    wget \
    && rm -rf /var/lib/apt/lists/*

RUN wget ${URL}
