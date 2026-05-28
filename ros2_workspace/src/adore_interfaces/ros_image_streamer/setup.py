from setuptools import setup

package_name = 'ros_image_streamer'

setup(
    name=package_name,
    version='1.0.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/config', [
            'config/streamer_config.yaml',
            'config/viewer_config.yaml',
        ]),
        ('share/' + package_name + '/launch', [
            'launch/streamer.launch.py',
            'launch/viewer.launch.py',
            'launch/streamer_and_viewer.launch.py',
        ]),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='maintainer',
    description='ROS 2 image streaming and viewing nodes',
    license='Apache-2.0',
    entry_points={
        'console_scripts': [
            'streaming_node = ros_image_streamer.streaming_node:main',
            'viewer_node = ros_image_streamer.viewer_node:main',
        ],
    },
)
