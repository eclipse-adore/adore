#!/usr/bin/env python3
"""Publish a ROS message to an MQTT topic on an interval.

    python3 scripts/mqtt_publish.py [topic] [--message TEXT] [--count N]
"""
import argparse
import os
import socket
import ssl
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mqtt_broker import describe, diagnose, load_settings, make_client, reason_text, setup_logging

log = setup_logging('mqtt_publish')


def _encode(text: str, fmt: str) -> bytes:
    """The ROS import is lazy so --format raw works without a sourced workspace."""
    if fmt == 'raw':
        return text.encode('utf-8')
    try:
        from rclpy.serialization import serialize_message
        from std_msgs.msg import String
    except ImportError as exc:
        raise SystemExit(f'--format cdr needs a sourced ROS 2 workspace ({exc}); '
                         f'use --format raw for opaque payloads')
    return serialize_message(String(data=text))


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('topic', nargs='?', default='mqtt/chatter')
    parser.add_argument('--config', default=None, help='bridge_config.yaml to read broker settings from')
    parser.add_argument('--message', default='Hello, MQTT!')
    parser.add_argument('--format', default='cdr', choices=('cdr', 'raw'))
    parser.add_argument('--count', type=int, default=0, help='messages to send (0 = run forever)')
    parser.add_argument('--interval', type=float, default=1.0)
    parser.add_argument('--qos', type=int, default=0, choices=(0, 1, 2))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    settings = load_settings(args.config)

    payload = _encode(args.message, args.format)
    client = make_client(settings, log=log)

    state = {'connected': False, 'attempts': 0}

    def on_connect(client, userdata, flags, reason_code, properties):
        if reason_code == 0:
            state['connected'] = True
            state['attempts'] = 0
            log.info('connected to %s', settings.address)
        else:
            log.error('broker %s refused the connection: %s', settings.address, reason_text(reason_code))
            client.disconnect()

    def on_disconnect(client, userdata, flags, reason_code, properties):
        if reason_code == 0:
            return
        state['attempts'] += 1
        log.warning('unexpected disconnect from %s: %s', settings.address, reason_text(reason_code))
        if not state['connected'] and state['attempts'] == 1:
            diagnose(settings, log)

    client.on_connect = on_connect
    client.on_disconnect = on_disconnect

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

    deadline = time.monotonic() + 10
    while not state['connected'] and time.monotonic() < deadline:
        time.sleep(0.1)
    if not state['connected']:
        log.error('no CONNACK from %s within 10s', settings.address)
        client.loop_stop()
        return 1

    sent = 0
    status = 0
    try:
        while not args.count or sent < args.count:
            info = client.publish(args.topic, payload, qos=args.qos)
            if args.qos:
                info.wait_for_publish(timeout=5)
            if info.rc != 0:
                log.error('publish to %s failed: %s', args.topic, reason_text(info.rc))
                status = 1
                break
            sent += 1
            log.info('published %d bytes to %s (%d total)', len(payload), args.topic, sent)
            if args.count and sent >= args.count:
                break
            time.sleep(args.interval)
    except KeyboardInterrupt:
        log.info('interrupted after %d message(s)', sent)
    finally:
        client.loop_stop()
        client.disconnect()

    return status


if __name__ == '__main__':
    sys.exit(main())
