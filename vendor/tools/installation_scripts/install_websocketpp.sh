#!/usr/bin/env bash


## install websocketpp

mkdir -p build
cd build
cmake ..
make build
make install
