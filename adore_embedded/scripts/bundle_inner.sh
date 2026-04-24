#!/usr/bin/env bash
# ********************************************************************************
# Copyright (c) 2026 Contributors to the Eclipse Foundation
#
# See the NOTICE file(s) distributed with this work for additional
# information regarding copyright ownership.
#
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# https://www.eclipse.org/legal/epl-2.0
#
# SPDX-License-Identifier: EPL-2.0
# ********************************************************************************

# Runs inside the unshare namespace. Args: <rootfs> <ros_distro> <workspace> [cmd...]
set -euo pipefail
ROOTFS="$1"; shift
ROS_DISTRO="$1"; shift
WORKSPACE="$1"; shift

mount -t proc  proc  "${ROOTFS}/proc"
mount --rbind  /sys  "${ROOTFS}/sys"
mount --rbind  /dev  "${ROOTFS}/dev"
mount --bind   "${WORKSPACE}" "${ROOTFS}/ros2_workspace_dist"

exec chroot "${ROOTFS}" /bin/bash -c '
    source /opt/ros/'"${ROS_DISTRO}"'/setup.bash
    source /ros2_workspace_dist/install/setup.bash 2>/dev/null || true
    exec "$@"
' -- "$@"
