#!/usr/bin/env python3
import os
import sys
import yaml


def env_or(cfg, key, default=None, env_var=None):
    name = cfg.get(f'{key}_env') or env_var
    if name:
        val = os.environ.get(name)
        if val is not None:
            return val
    return cfg.get(key, default)


def load_env_file(path):
    if not path or not os.path.exists(path):
        return
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            key, _, value = line.partition('=')
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def main():
    config_path = sys.argv[1]
    with open(config_path) as f:
        cfg = yaml.safe_load(f) or {}
    mqtt = cfg.get('mqtt', {})

    env_file = mqtt.get('env_file')
    if env_file and not os.path.isabs(env_file):
        env_file = os.path.join(os.path.dirname(os.path.abspath(config_path)), env_file)
    load_env_file(env_file)

    cert_dir = os.environ.get('MQTT_BRIDGE_CERT_DIR', '')

    def resolve(path):
        if not path or os.path.isabs(path):
            return path
        return os.path.join(cert_dir, path)

    args = ['-h', str(env_or(mqtt, 'host', 'localhost', 'MQTT_HOST')),
            '-p', str(env_or(mqtt, 'port', 1883, 'MQTT_PORT'))]

    auth = mqtt.get('auth') or {}
    user_env = auth.get('username_env', 'MQTT_USERNAME')
    pass_env = auth.get('password_env', 'MQTT_PASSWORD')
    username = os.environ.get(user_env) if user_env else None
    password = os.environ.get(pass_env) if pass_env else None
    if username:
        args += ['-u', username]
    if password:
        args += ['-P', password]

    tls = mqtt.get('tls') or {}
    enabled = env_or(tls, 'enabled', False, 'MQTT_TLS')
    if isinstance(enabled, str):
        enabled = enabled.lower() in ('1', 'true', 'yes')
    if enabled:
        ca_certs = resolve(env_or(tls, 'ca_certs', env_var='MQTT_CA_CERT'))
        certfile = resolve(env_or(tls, 'certfile', env_var='MQTT_CLIENT_CERT'))
        keyfile = resolve(env_or(tls, 'keyfile', env_var='MQTT_CLIENT_KEY'))
        if ca_certs:
            args += ['--cafile', ca_certs]
        else:
            args += ['--capath', '/etc/ssl/certs']
        if certfile:
            args += ['--cert', certfile]
        if keyfile:
            args += ['--key', keyfile]
        if tls.get('insecure'):
            args += ['--insecure']

    for arg in args:
        sys.stdout.write(arg + '\0')


if __name__ == '__main__':
    main()
