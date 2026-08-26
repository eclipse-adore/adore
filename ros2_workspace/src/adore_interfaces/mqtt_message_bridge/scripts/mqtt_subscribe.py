#!/usr/bin/env python3
"""Subscribe to an MQTT topic and print each payload.

Broker settings come from config/bridge_config.yaml, so TLS and credentials
match the bridge node. Environment variables still win over the file.

    python3 scripts/mqtt_subscribe.py [topic] [--format raw|cdr] [--count N]
"""
import argparse
import os
import socket
import ssl
import sys
import threading

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mqtt_broker import (
    describe,
    diagnose,
    is_auth_failure,
    load_settings,
    make_client,
    reason_text,
    setup_logging,
)

MAX_ATTEMPTS = 3
CONNECT_TIMEOUT = 15

log = setup_logging('mqtt_subscribe')


def cdr_decoder():
    """Imported lazily so --format raw works without a sourced ROS workspace."""
    try:
        from rclpy.serialization import deserialize_message
        from std_msgs.msg import String
    except ImportError as exc:
        raise SystemExit(f'--format cdr needs a sourced ROS 2 workspace ({exc}); '
                         f'use --format raw for opaque payloads')
    return lambda payload: deserialize_message(payload, String).data


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('topic', nargs='?', default='mqtt/chatter')
    parser.add_argument('--config', default=None, help='bridge config to read broker settings from')
    parser.add_argument('--format', default='cdr', choices=('cdr', 'raw'),
                        help='cdr deserializes a std_msgs/String, raw prints the payload as text')
    parser.add_argument('--count', type=int, default=0, help='exit after N messages (0 = run forever)')
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    settings = load_settings(args.config)
    decode = cdr_decoder() if args.format == 'cdr' else None
    state = {'received': 0, 'attempts': 0, 'diagnosed': False}
    connected = threading.Event()
    done = threading.Event()

    client = make_client(settings, log=log)

    def on_connect(client, userdata, flags, reason_code, properties):
        if reason_code == 0:
            connected.set()
            state['attempts'] = 0
            log.info('connected to %s, subscribing to %s', settings.address, args.topic)
            client.subscribe(args.topic)
            return
        log.error('broker %s refused the connection: %s', settings.address, reason_text(reason_code))
        if is_auth_failure(reason_code):
            log.error('check MQTT_USERNAME/MQTT_PASSWORD, the client certificate and the broker ACL')
        done.set()

    def on_disconnect(client, userdata, flags, reason_code, properties):
        if reason_code == 0:
            log.info('disconnected from %s', settings.address)
            return
        state['attempts'] += 1
        log.warning('unexpected disconnect from %s: %s', settings.address, reason_text(reason_code))
        if connected.is_set():
            return
        if not state['diagnosed']:
            diagnose(settings, log)
            state['diagnosed'] = True
        if state['attempts'] >= MAX_ATTEMPTS and not done.is_set():
            log.error('giving up after %d failed connection attempts', state['attempts'])
            done.set()

    def on_subscribe(client, userdata, mid, reason_codes, properties):
        for rc in reason_codes:
            if rc.is_failure:
                log.error('broker %s denied SUBSCRIBE for %s: %s',
                          settings.address, args.topic, reason_text(rc))
            else:
                log.info('subscribed to %s (qos %s)', args.topic, rc.value)

    def on_message(client, userdata, message):
        state['received'] += 1
        if decode is None:
            text = message.payload.decode('utf-8', errors='replace')
        else:
            try:
                text = decode(message.payload)
            except Exception:
                log.exception('failed to deserialize %d byte payload on %s; try --format raw',
                              len(message.payload), message.topic)
                return
        print(f'[{message.topic}] {text}', flush=True)
        if args.count and state['received'] >= args.count:
            done.set()

    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_subscribe = on_subscribe
    client.on_message = on_message

    log.info('connecting: %s', describe(settings))
    if settings.missing:
        log.error('TLS material missing on disk: %s', ', '.join(settings.missing))
        return 1

    try:
        client.connect(settings.host, settings.port, settings.keepalive)
    except socket.gaierror as exc:
        log.error('cannot resolve host %r: %s', settings.host, exc)
        diagnose(settings, log)
        return 1
    except ssl.SSLError as exc:
        log.error('TLS handshake with %s failed: %s', settings.address, exc)
        diagnose(settings, log)
        return 1
    except OSError as exc:
        log.error('cannot reach broker at %s: %s', settings.address, exc)
        diagnose(settings, log)
        return 1

    client.loop_start()
    try:
        if not connected.wait(CONNECT_TIMEOUT) and not done.is_set():
            log.error('no CONNACK from %s within %ss', settings.address, CONNECT_TIMEOUT)
            diagnose(settings, log)
            return 1
        done.wait()
    except KeyboardInterrupt:
        log.info('interrupted after %d message(s)', state['received'])
    finally:
        client.loop_stop()
        client.disconnect()

    if not connected.is_set():
        return 1
    return 0 if state['received'] or not args.count else 1


if __name__ == '__main__':
    sys.exit(main())
