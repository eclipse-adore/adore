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

from setuptools import setup, find_packages
import os

package_name = os.path.basename(os.path.dirname(os.path.abspath(__file__)))

requirements = []
if os.path.exists('requirements.pip3'):
    with open('requirements.pip3', 'r') as f:
        requirements = [line.strip() for line in f if line.strip() and not line.strip().startswith('#')]

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    data_files=[
        ('share/ament_index/resource_index/packages', [os.path.join('resource', package_name)]),
        (f'share/{package_name}', ['package.xml']),
    ],
    install_requires=requirements,
    python_requires='>=3.6',
    zip_safe=True,
    maintainer='Your Name',
    maintainer_email='you@example.com',
    description='ROS 2 Python Hello World example with NumPy',
    license='Apache-2.0',
    entry_points={
        'console_scripts': [
            f'{package_name} = {package_name}.hello_world_node:main',
            f'{package_name}_adore = {package_name}.adore_hello_world_node:main',
        ],
    },
    extras_require={
        'test': ['pytest']
    },
)

