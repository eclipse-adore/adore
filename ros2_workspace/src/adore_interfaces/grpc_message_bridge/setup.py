from setuptools import setup

package_name = 'grpc_message_bridge'

setup(
    name=package_name,
    version='1.0.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/config', ['config/bridge_config.yaml']),
        ('share/' + package_name + '/launch', ['launch/bridge.launch.py']),
    ],
    install_requires=['setuptools', 'grpcio', 'grpcio-tools', 'pyyaml'],
    zip_safe=True,
    maintainer='akoerner',
    description='ROS 2 gRPC Message Bridge',
    license='Apache-2.0',
    entry_points={
        'console_scripts': [
            'bridge_node = grpc_message_bridge.bridge_node:main'
        ],
    },
)
