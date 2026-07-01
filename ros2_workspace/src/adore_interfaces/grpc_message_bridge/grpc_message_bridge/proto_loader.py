import importlib.util
import logging
import os
import subprocess
import sys
from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional

import yaml

log = logging.getLogger(__name__)

_CUSTOM_PROTOS_DIR = os.path.join(os.path.dirname(__file__), '..', 'custom_protos')
_REGISTRY_PATH    = os.path.join(_CUSTOM_PROTOS_DIR, 'registry.yaml')


@dataclass
class CustomServiceSpec:
    proto_module:   str
    service_name:   str
    stub_class:     str
    servicer_base:  str
    publish_rpc:    str
    subscribe_rpc:  str
    message_class:  str
    ack_class:      str

    pb2_mod:      Any = None
    pb2_grpc_mod: Any = None

    @property
    def stub(self):
        return getattr(self.pb2_grpc_mod, self.stub_class)

    @property
    def servicer(self):
        return getattr(self.pb2_grpc_mod, self.servicer_base)

    @property
    def add_servicer_fn(self) -> Callable:
        fn_name = f'add_{self.servicer_base}_to_server'
        return getattr(self.pb2_grpc_mod, fn_name)

    @property
    def message_cls(self):
        return getattr(self.pb2_mod, self.message_class)

    @property
    def ack_cls(self):
        return getattr(self.pb2_mod, self.ack_class)


_registry: Dict[str, CustomServiceSpec] = {}


def _compile_proto(proto_path: str, out_dir: str) -> bool:
    result = subprocess.run(
        [
            sys.executable, '-m', 'grpc_tools.protoc',
            f'-I{os.path.dirname(proto_path)}',
            f'--python_out={out_dir}',
            f'--grpc_python_out={out_dir}',
            proto_path,
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        log.error('protoc failed for %s:\n%s', proto_path, result.stderr)
        return False
    return True


def _fix_grpc_imports(grpc_py_path: str) -> None:
    """Rewrite absolute pb2 imports to relative so modules load from custom_protos/."""
    with open(grpc_py_path, 'r') as f:
        src = f.read()
    lines = []
    for line in src.splitlines():
        if line.startswith('import ') and line.endswith('_pb2'):
            mod = line.split()[1]
            line = f'from . import {mod}'
        lines.append(line)
    with open(grpc_py_path, 'w') as f:
        f.write('\n'.join(lines))


def _load_module(name: str, path: str):
    spec   = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def load_custom_protos(custom_protos_dir: Optional[str] = None) -> Dict[str, CustomServiceSpec]:
    global _registry
    protos_dir   = os.path.abspath(custom_protos_dir or _CUSTOM_PROTOS_DIR)
    registry_path = os.path.join(protos_dir, 'registry.yaml')

    if not os.path.isdir(protos_dir):
        log.debug('custom_protos directory not found, skipping: %s', protos_dir)
        return _registry

    if not os.path.isfile(registry_path):
        log.debug('no registry.yaml in %s, skipping custom protos', protos_dir)
        return _registry

    with open(registry_path) as f:
        registry_data = yaml.safe_load(f) or {}

    services = registry_data.get('services') or []
    if not services:
        log.debug('registry.yaml has no services entries')
        return _registry

    # Ensure the protos dir is importable so relative imports in generated code work.
    init_path = os.path.join(protos_dir, '__init__.py')
    if not os.path.exists(init_path):
        open(init_path, 'w').close()

    if protos_dir not in sys.path:
        sys.path.insert(0, os.path.dirname(protos_dir))

    for entry in services:
        mod_name    = entry['proto_module']          # e.g. example_sensor_pb2
        base_name   = mod_name.replace('_pb2', '')   # e.g. example_sensor
        pb2_path    = os.path.join(protos_dir, f'{mod_name}.py')
        pb2_grpc_path = os.path.join(protos_dir, f'{base_name}_pb2_grpc.py')

        if not os.path.exists(pb2_path):
            proto_file = os.path.join(protos_dir, f'{base_name}.proto')
            if not os.path.exists(proto_file):
                log.error('proto file not found: %s', proto_file)
                continue
            log.info('compiling %s', proto_file)
            if not _compile_proto(proto_file, protos_dir):
                continue
            if os.path.exists(pb2_grpc_path):
                _fix_grpc_imports(pb2_grpc_path)

        try:
            pkg_prefix  = f'custom_protos.{mod_name}'
            pb2_mod     = _load_module(pkg_prefix, pb2_path)
            grpc_prefix = f'custom_protos.{base_name}_pb2_grpc'
            pb2_grpc_mod = _load_module(grpc_prefix, pb2_grpc_path)
        except Exception as e:
            log.error('failed to load %s: %s', mod_name, e)
            continue

        spec = CustomServiceSpec(
            proto_module   = mod_name,
            service_name   = entry['service_name'],
            stub_class     = entry['stub_class'],
            servicer_base  = entry['servicer_base'],
            publish_rpc    = entry['publish_rpc'],
            subscribe_rpc  = entry['subscribe_rpc'],
            message_class  = entry['message_class'],
            ack_class      = entry['ack_class'],
            pb2_mod        = pb2_mod,
            pb2_grpc_mod   = pb2_grpc_mod,
        )
        _registry[entry['service_name']] = spec
        log.info('registered custom gRPC service: %s', entry['service_name'])

    return _registry


def get_service(service_name: str) -> Optional[CustomServiceSpec]:
    return _registry.get(service_name)
