#!/usr/bin/env python3
"""Emit NUL-separated mosquitto_pub/mosquitto_sub arguments for a bridge config.

Consumed by mqtt_common.sh so the shell tooling connects exactly like the node.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mqtt_broker import load_settings


def broker_args(settings) -> list:
    args = ['-h', settings.host, '-p', str(settings.port), '-q', str(settings.qos)]
    if settings.username:
        args += ['-u', settings.username]
    if settings.password:
        args += ['-P', settings.password]
    if settings.tls:
        if settings.ca_certs:
            args += ['--cafile', settings.ca_certs]
        else:
            args += ['--capath', '/etc/ssl/certs']
        if settings.certfile:
            args += ['--cert', settings.certfile]
        if settings.keyfile:
            args += ['--key', settings.keyfile]
        if settings.insecure:
            args += ['--insecure']
    return args


def main():
    settings = load_settings(sys.argv[1] if len(sys.argv) > 1 else None)
    if settings.missing:
        print(f'ERROR: TLS material missing: {", ".join(settings.missing)}', file=sys.stderr)
        return 1
    for arg in broker_args(settings):
        sys.stdout.write(arg + '\0')
    return 0


if __name__ == '__main__':
    sys.exit(main())
