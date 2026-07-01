import os
import subprocess

from setuptools import find_packages, setup
from setuptools.command.build_py import build_py

package_name = 'grpc_message_bridge'
here = os.path.abspath(os.path.dirname(__file__))


class GenProto(build_py):
    """Generate gRPC stubs from the proto submodule before packaging.

    Runs as part of `colcon build` so a checkout with the proto submodule
    initialised produces a working package with no manual `make gen_proto`.
    """

    def run(self):
        proto_root = os.environ.get('GRPC_BRIDGE_PROTO_ROOT', os.path.join(here, 'proto'))
        proto_out = os.path.join(here, 'proto', 'generated')
        subprocess.check_call(
            ['make', 'gen_proto', f'PROTO_ROOT={proto_root}', f'PROTO_OUT={proto_out}'],
            cwd=here,
        )
        super().run()


setup(
    name    = package_name,
    version = '2.0.0',
    packages = find_packages(exclude=['test']),
    cmdclass = {'build_py': GenProto},
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
