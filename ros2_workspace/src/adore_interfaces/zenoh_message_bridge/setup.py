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

from setuptools import setup
import os
from glob import glob

package_name = 'zenoh_message_bridge'

setup(
    name=package_name,
    version='1.0.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'config'), glob('config/*.yaml')),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.py')),
    ],
    install_requires=['setuptools', 'yq', 'eclipse-zenoh'],
    zip_safe=True,
    maintainer='User',
    description='ROS 2 Zenoh Bridge',
    license='Apache-2.0',
    entry_points={
        'console_scripts': [
            'bridge_node = zenoh_message_bridge.bridge_node:main'
        ],
    },
)
