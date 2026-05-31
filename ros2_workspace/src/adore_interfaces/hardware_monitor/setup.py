from setuptools import setup

package_name = 'hardware_monitor'

setup(
    name=package_name,
    version='1.0.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/config', ['config/hardware_monitor.yaml']),
        ('share/' + package_name + '/launch', ['launch/hardware_monitor.launch.py']),
    ],
    install_requires=['setuptools', 'psutil'],
    zip_safe=True,
    maintainer='maintainer',
    description='ROS 2 hardware discovery and status monitoring nodes',
    license='Apache-2.0',
    entry_points={
        'console_scripts': [
            'hardware_discovery_node = hardware_monitor.hardware_discovery_node:main',
            'hardware_status_node = hardware_monitor.hardware_status_node:main',
        ],
    },
)
