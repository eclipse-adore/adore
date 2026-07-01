from setuptools import setup, find_packages

package_name = 'grpc_message_bridge'

setup(
    name    = package_name,
    version = '2.0.0',
    packages = find_packages(exclude=['test']),
    data_files = [
        ('share/ament_index/resource_index/packages', ['resource/grpc_message_bridge']),
        ('share/' + package_name,                     ['package.xml']),
        ('share/' + package_name + '/config',         ['config/bridge_config.yaml']),
        ('share/' + package_name + '/launch',         ['launch/bridge.launch.py']),
    ],
    install_requires = ['setuptools', 'grpcio', 'grpcio-tools', 'pyyaml', 'protobuf'],
    zip_safe   = True,
    maintainer = 'motorai',
    license    = 'Apache-2.0',
    entry_points = {
        'console_scripts': [
            'bridge_node = grpc_message_bridge.bridge_node:main',
        ],
    },
)
