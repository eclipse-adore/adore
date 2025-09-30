# ********************************************************************************
# Copyright (c) 2025 Contributors to the Eclipse Foundation
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


import psutil


def kill_process_and_children(pid):
    """Ensure all child processes of a launch file are killed."""
    try:
        parent = psutil.Process(pid)
        children = parent.children(recursive=True)  # Get all child processes
        for child in children:
            child.terminate()
        gone, alive = psutil.wait_procs(children, timeout=5)
        for child in alive:
            child.kill()  # Force kill if still alive
        parent.terminate()
        parent.wait(5)
    except psutil.NoSuchProcess:
        pass