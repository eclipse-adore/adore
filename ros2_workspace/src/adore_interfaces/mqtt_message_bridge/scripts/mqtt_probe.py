#!/usr/bin/env python3
"""Probe a broker one layer at a time so a failure names the layer that broke.

    python3 scripts/mqtt_probe.py --stage tcp|tls|auth [--config PATH]

Prints a single line describing the outcome. Exit codes: 0 pass, 1 fail,
2 not applicable (for example TLS when the config does not enable it).
"""
import argparse
import os
import socket
import ssl
import sys
import threading

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mqtt_broker import load_settings, make_client, reason_text

TIMEOUT = 10
NOT_APPLICABLE = 2


def stage_tcp(settings):
    try:
        with socket.create_connection((settings.host, settings.port), timeout=TIMEOUT):
            return 0, f'{settings.address} accepted a TCP connection'
    except socket.gaierror as exc:
        return 1, f'cannot resolve {settings.host!r}: {exc}'
    except OSError as exc:
        return 1, f'cannot reach {settings.address}: {exc}'


def _cert_summary(cert) -> str:
    if not cert:
        return 'server certificate not verified (insecure mode)'
    subject = dict(x[0] for x in cert.get('subject', ()))
    issuer = dict(x[0] for x in cert.get('issuer', ()))
    return (f'server CN={subject.get("commonName", "?")} '
            f'issuer={issuer.get("commonName", "?")} expires={cert.get("notAfter", "?")}')


def stage_tls(settings):
    if not settings.tls:
        return NOT_APPLICABLE, 'TLS is not enabled in the config'
    if settings.missing:
        return 1, f'TLS material missing on disk: {", ".join(settings.missing)}'

    try:
        context = ssl.create_default_context(cafile=settings.ca_certs)
    except OSError as exc:
        return 1, f'cannot load CA file {settings.ca_certs}: {exc}'
    if settings.insecure:
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
    if settings.certfile:
        try:
            context.load_cert_chain(settings.certfile, settings.keyfile)
        except (OSError, ssl.SSLError) as exc:
            return 1, f'cannot load client certificate {settings.certfile}: {exc}'

    try:
        with socket.create_connection((settings.host, settings.port), timeout=TIMEOUT) as raw:
            with context.wrap_socket(raw, server_hostname=settings.host) as tls:
                return 0, f'{tls.version()} handshake completed, {_cert_summary(tls.getpeercert())}'
    except ssl.SSLCertVerificationError as exc:
        return 1, (f'server certificate rejected: {exc.verify_message or exc}; '
                   f'check mqtt.tls.ca_certs ({settings.ca_certs or "system store"})')
    except ssl.SSLError as exc:
        return 1, (f'TLS handshake with {settings.address} failed: {exc}; '
                   f'the port may not be a TLS listener, or the client certificate was rejected')
    except OSError as exc:
        return 1, f'TLS handshake with {settings.address} failed at the transport: {exc}'


def stage_auth(settings):
    result = {'code': None}
    done = threading.Event()

    def on_connect(client, userdata, flags, reason_code, properties):
        result['code'] = reason_code
        done.set()

    client = make_client(settings)
    client.on_connect = on_connect
    try:
        client.connect(settings.host, settings.port, settings.keepalive)
    except OSError as exc:
        return 1, f'connection to {settings.address} failed before CONNACK: {exc}'

    client.loop_start()
    try:
        if not done.wait(TIMEOUT):
            return 1, f'no CONNACK from {settings.address} within {TIMEOUT}s'
        code = result['code']
        if code == 0:
            identity = settings.username or 'anonymous'
            return 0, f'{settings.address} accepted the session as {identity}'
        return 1, (f'{settings.address} refused the session: {reason_text(code)}; '
                   f'check the username, password, client certificate and broker ACL')
    finally:
        client.loop_stop()
        client.disconnect()


STAGES = {'tcp': stage_tcp, 'tls': stage_tls, 'auth': stage_auth}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stage', required=True, choices=sorted(STAGES))
    parser.add_argument('--config', default=None)
    args = parser.parse_args()

    settings = load_settings(args.config)
    status, message = STAGES[args.stage](settings)
    print(message)
    return status


if __name__ == '__main__':
    sys.exit(main())
