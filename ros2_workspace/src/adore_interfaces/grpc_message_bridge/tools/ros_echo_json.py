#!/usr/bin/env python3
"""
Echo the bridge's ROS topics with each String payload parsed as JSON.

    ros2 run --prefix 'python3' ...   # not needed, just run it directly
    python3 tools/ros_echo_json.py [--topic T ...] [--compact] [--field F ...]
"""

import argparse
import json
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'proto', 'generated'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import rclpy
from rclpy.node import Node
from rclpy.qos import DurabilityPolicy, HistoryPolicy, QoSProfile, ReliabilityPolicy
from std_msgs.msg import String

_DEFAULT_TOPICS = [
    '/supervision/telemetry',
    '/supervision/notifications',
    '/supervision/ack/rx',
    '/supervision/signaling/rx',
]


def _topics():
    try:
        from grpc_message_bridge.proto_registry import STREAMS
        stream = STREAMS['client.ClientService.ClientStream']
        return [fm.ros_topic for fm in stream.recv_fields]
    except Exception:
        return _DEFAULT_TOPICS


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--topic', action='append', dest='topics',
                    help='Topic to echo, repeatable. Default: all bridge recv topics.')
    ap.add_argument('--field', action='append', dest='fields',
                    help='Print only these top-level JSON keys, repeatable.')
    ap.add_argument('--compact', action='store_true', help='One line per message.')
    args = ap.parse_args()

    topics = args.topics or _topics()

    rclpy.init()
    node = Node('ros_echo_json')
    qos = QoSProfile(
        depth       = 10,
        history     = HistoryPolicy.KEEP_LAST,
        reliability = ReliabilityPolicy.RELIABLE,
        durability  = DurabilityPolicy.VOLATILE,
    )

    width = max(len(t) for t in topics)
    seen  = {t: 0 for t in topics}

    def on_msg(msg, topic):
        seen[topic] += 1
        stamp = time.strftime('%H:%M:%S')
        try:
            payload = json.loads(msg.data)
        except ValueError:
            print(f'[{stamp}] {topic:<{width}} #{seen[topic]} <not json> {msg.data}',
                  flush=True)
            return

        if args.fields and isinstance(payload, dict):
            payload = {k: payload[k] for k in args.fields if k in payload}

        body = (json.dumps(payload) if args.compact
                else json.dumps(payload, indent=2, sort_keys=True))
        print(f'[{stamp}] {topic:<{width}} #{seen[topic]}', flush=True)
        print(body if args.compact is False else f'  {body}', flush=True)

    for topic in topics:
        node.create_subscription(String, topic,
                                 lambda m, t=topic: on_msg(m, t), qos)

    print(f'Echoing {len(topics)} topic(s) as JSON, Ctrl-C to stop:', file=sys.stderr)
    for topic in topics:
        print(f'  {topic}', file=sys.stderr)

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        print('\nmessages per topic: '
              + ', '.join(f'{t}={n}' for t, n in seen.items()), file=sys.stderr)
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
