#!/usr/bin/env bash
ros2 topic echo --field data /cluster/hardware_inventory | grep -v "^---"
