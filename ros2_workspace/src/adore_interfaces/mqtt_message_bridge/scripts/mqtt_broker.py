"""Broker connection settings for the standalone scripts.

Reads the same bridge_config.yaml the node uses so the scripts and the bridge
never disagree about host, port, credentials or TLS material.
Precedence: process environment > env_file named in the config > config values.
"""
import logging
import os
import sys
from dataclasses import dataclass, field

import paho.mqtt.client as mqtt
import yaml

PROTOCOLS = {
    'mqtt': mqtt.MQTTv311,
    'mqttv5': mqtt.MQTTv5,
}


def package_root(start_path: str) -> str | None:
    directory = os.path.dirname(os.path.realpath(start_path))
    while True:
        if os.path.isfile(os.path.join(directory, 'package.xml')):
            return directory
        parent = os.path.dirname(directory)
        if parent == directory:
            return None
        directory = parent


PKG_ROOT = package_root(__file__) or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_CONFIG = os.path.join(PKG_ROOT, 'config', 'bridge_config.yaml')

sys.path.insert(0, PKG_ROOT)
from mqtt_message_bridge.diagnostics import (  # noqa: E402
    failure_hints,
    is_auth_failure,
    port_speaks_tls,
    reason_text,
)


def load_env_file(path: str | None) -> None:
    if not path or not os.path.exists(path):
        return
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            key, _, value = line.partition('=')
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def env_or(cfg: dict, key: str, default=None, env_var: str | None = None):
    name = cfg.get(f'{key}_env') or env_var
    if name:
        value = os.environ.get(name)
        if value is not None:
            return value
    return cfg.get(key, default)


def as_bool(value) -> bool:
    if isinstance(value, str):
        return value.strip().lower() in ('1', 'true', 'yes', 'on')
    return bool(value)


@dataclass
class BrokerSettings:
    host: str = 'localhost'
    port: int = 1883
    keepalive: int = 60
    transport: str = 'tcp'
    protocol: int = mqtt.MQTTv311
    username: str | None = None
    password: str | None = None
    tls: bool = False
    ca_certs: str | None = None
    certfile: str | None = None
    keyfile: str | None = None
    insecure: bool = False
    qos: int = 0
    config_path: str | None = None
    missing: list = field(default_factory=list)

    @property
    def address(self) -> str:
        return f'{self.host}:{self.port}'


def _resolve(path: str | None, cert_dir: str) -> str | None:
    if not path or os.path.isabs(path):
        return path
    return os.path.join(cert_dir, path)


def load_settings(config_path: str | None = None) -> BrokerSettings:
    config_path = config_path or os.environ.get('MQTT_BRIDGE_CONFIG') or DEFAULT_CONFIG
    cfg = {}
    if os.path.exists(config_path):
        with open(config_path) as f:
            cfg = yaml.safe_load(f) or {}
    mqtt_cfg = cfg.get('mqtt') or {}

    env_file = mqtt_cfg.get('env_file')
    if env_file and not os.path.isabs(env_file):
        base = package_root(config_path) or os.path.dirname(os.path.abspath(config_path))
        env_file = os.path.normpath(os.path.join(base, env_file))
    load_env_file(env_file)

    cert_dir = os.environ.get('MQTT_BRIDGE_CERT_DIR') or os.path.join(PKG_ROOT, 'certs')

    auth = mqtt_cfg.get('auth') or {}
    tls_cfg = mqtt_cfg.get('tls') or {}

    settings = BrokerSettings(
        host=str(env_or(mqtt_cfg, 'host', 'localhost', 'MQTT_HOST')),
        port=int(env_or(mqtt_cfg, 'port', 1883, 'MQTT_PORT')),
        keepalive=int(env_or(mqtt_cfg, 'keepalive', 60, 'MQTT_KEEPALIVE')),
        qos=int(env_or(mqtt_cfg, 'qos', 0, 'MQTT_QOS')),
        transport=str(env_or(mqtt_cfg, 'transport', 'tcp')),
        protocol=PROTOCOLS.get(str(env_or(mqtt_cfg, 'protocol', 'mqtt')), mqtt.MQTTv311),
        username=os.environ.get(auth.get('username_env', 'MQTT_USERNAME')),
        password=os.environ.get(auth.get('password_env', 'MQTT_PASSWORD')),
        tls=as_bool(env_or(tls_cfg, 'enabled', False, 'MQTT_TLS')),
        ca_certs=_resolve(env_or(tls_cfg, 'ca_certs', env_var='MQTT_CA_CERT'), cert_dir),
        certfile=_resolve(env_or(tls_cfg, 'certfile', env_var='MQTT_CLIENT_CERT'), cert_dir),
        keyfile=_resolve(env_or(tls_cfg, 'keyfile', env_var='MQTT_CLIENT_KEY'), cert_dir),
        insecure=as_bool(tls_cfg.get('insecure', False)),
        config_path=config_path if os.path.exists(config_path) else None,
    )

    if settings.tls:
        settings.missing = [
            p for p in (settings.ca_certs, settings.certfile, settings.keyfile)
            if p and not os.path.exists(p)
        ]
    return settings


def make_client(settings: BrokerSettings, client_id: str = '', log: logging.Logger | None = None) -> mqtt.Client:
    client = mqtt.Client(
        mqtt.CallbackAPIVersion.VERSION2,
        client_id=client_id,
        protocol=settings.protocol,
        transport=settings.transport,
    )
    if settings.username:
        client.username_pw_set(settings.username, settings.password)
    if settings.tls:
        client.tls_set(
            ca_certs=settings.ca_certs,
            certfile=settings.certfile,
            keyfile=settings.keyfile,
        )
        if settings.insecure:
            client.tls_insecure_set(True)
    if log is not None:
        client.enable_logger(log)
    return client


def describe(settings: BrokerSettings) -> str:
    parts = [
        f'broker={settings.address}',
        f'tls={"on" if settings.tls else "off"}',
        f'transport={settings.transport}',
        f'user={settings.username or "<anonymous>"}',
        f'config={settings.config_path or "<none, using defaults/env>"}',
    ]
    if settings.tls:
        parts.append(f'ca={settings.ca_certs or "system"}')
        parts.append(f'cert={settings.certfile or "<none>"}')
    return ' '.join(parts)


def diagnose(settings: BrokerSettings, log: logging.Logger) -> None:
    """Explain a failed connection in terms of what the port actually offers."""
    log.error('connection settings: %s', describe(settings))
    for hint in failure_hints(settings.host, settings.port, settings.tls, settings.missing):
        log.error('%s', hint)


def setup_logging(name: str) -> logging.Logger:
    logging.basicConfig(
        level=os.environ.get('LOG_LEVEL', 'INFO').upper(),
        format='%(asctime)s %(levelname)s %(message)s',
        stream=sys.stdout,
    )
    return logging.getLogger(name)
