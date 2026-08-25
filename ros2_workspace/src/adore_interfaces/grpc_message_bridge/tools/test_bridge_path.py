#!/usr/bin/env python3
"""
Drives the bridge's own codec + proto_registry + auth through the full
subscribe path without a ROS runtime, so gRPC-side and ROS-side failures
can be told apart.

    set -a && source .secrets.env && set +a
    PYTHONPATH=proto/generated:. python3 tools/test_bridge_path.py
"""

import json
import logging
import os
import queue
import sys
import threading
import time

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_ROOT, 'proto', 'generated'))
sys.path.insert(0, _ROOT)

logging.basicConfig(level=logging.INFO, format='[%(name)s] %(levelname)s %(message)s')

import grpc
from std_msgs.msg import String

from grpc_message_bridge.auth import make_channel
from grpc_message_bridge.codec import (
    active_oneof_field,
    load_ros_type,
    make_ros_deserializer,
    make_ros_serializer,
    proto_field_set,
    proto_field_to_bytes,
    wire_ros_type,
)
from grpc_message_bridge.proto_registry import STREAMS

STREAM_KEY = 'client.ClientService.ClientStream'
SUB_TOPIC = '/supervision/subscription'
DURATION_S = 15


def main() -> int:
    stream = STREAMS[STREAM_KEY]

    import grpc_message_bridge.codec as _codec
    print(f'codec     {_codec.__file__}')
    if not _codec.__file__.startswith(_ROOT):
        print(f'WARNING   imported from outside {_ROOT}, a stale build copy is shadowing src')

    print(f'endpoint  {os.environ.get("GRPC_ENDPOINT", "<unset>")}')
    print(f'auth      {os.environ.get("AUTH_ENDPOINT", "<unset>")}')
    if not os.environ.get('AUTH_ENDPOINT'):
        print('AUTH_ENDPOINT unset, make_channel will fall back to insecure')

    send_fm = next(fm for fm in stream.send_fields if fm.ros_topic == SUB_TOPIC)
    wire_type = wire_ros_type(send_fm.ros_msg_type, send_fm.format)
    serialize = make_ros_serializer(wire_type, send_fm.format)

    ros_msg = String(data=json.dumps({'type': 'TELEMETRY', 'vehicleIds': []}))
    payload = serialize(ros_msg)
    print(f'\npayload   {payload!r}')

    sub_msg = proto_field_set(stream.send_msg_cls, send_fm.field_name, payload, send_fm.format)
    print('packed    ' + (str(sub_msg).strip().replace('\n', '\n          ') or '<all defaults>'))
    if active_oneof_field(sub_msg) != send_fm.field_name:
        print(f'FAIL      oneof is {active_oneof_field(sub_msg)!r}, expected {send_fm.field_name!r}')
        return 1

    send_q = queue.Queue()
    send_q.put(sub_msg)
    stop = threading.Event()

    def sender():
        while not stop.is_set():
            try:
                yield send_q.get(timeout=0.5)
            except queue.Empty:
                continue

    channel = make_channel()
    stub = stream.stub_cls(channel)
    rpc = getattr(stub, stream.rpc)

    counts = {}
    published = 0
    started = time.monotonic()
    print(f'\nstreaming for {DURATION_S}s\n')

    try:
        for server_msg in rpc(sender(), timeout=DURATION_S):
            field = active_oneof_field(server_msg)
            counts[field] = counts.get(field, 0) + 1

            fm = stream.recv_field_map.get(field)
            if fm is None:
                print(f'  {field:<16} no recv_field_map entry, dropped')
            else:
                data = proto_field_to_bytes(server_msg, field, fm.format)
                if data is None:
                    print(f'  {field:<16} proto_field_to_bytes returned None')
                else:
                    ros_type = load_ros_type(wire_ros_type(fm.ros_msg_type, fm.format))
                    try:
                        out = make_ros_deserializer(ros_type, fm.format)(data)
                        if published < 3:
                            print(f'  {field:<16} -> {fm.ros_topic}  {out}')
                        published += 1
                    except Exception as e:
                        print(f'  {field:<16} deser failed: {type(e).__name__}: {e}')

    except grpc.RpcError as e:
        if e.code() is not grpc.StatusCode.DEADLINE_EXCEEDED:
            print(f'\nstream error: {e.code().name}: {e.details()}')
            return 1
    except Exception as e:
        print(f'\nstream error: {type(e).__name__}: {e}')
        return 1
    finally:
        stop.set()
        channel.close()

    print(f'\nelapsed   {time.monotonic() - started:.1f}s')
    print(f'received  {counts or "nothing"}')
    print(f'publishable {published}')

    if not counts:
        print('\ngRPC side is the problem, the gateway sent nothing on this stream')
        return 1
    if not published:
        print('\ncodec is the problem, messages arrived but none survived conversion')
        return 1
    print('\ngRPC and codec both fine, remaining fault is in the ROS publish path')
    return 0


if __name__ == '__main__':
    sys.exit(main())
