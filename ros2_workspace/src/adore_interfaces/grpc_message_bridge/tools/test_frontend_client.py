#!/usr/bin/env python3
"""
Simulates a frontend client connecting to the bridge.

Subscribes to ALL telemetry and notifications, prints what it receives,
and optionally sends a test subscription request.

Usage:
    python3 scripts/test_frontend_client.py [--address localhost:50051]
"""
import argparse
import sys
import os
import time

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, '..', 'proto', 'generated'))

import grpc
from client import stream_pb2, stream_pb2_grpc
from messages import common_pb2

parser = argparse.ArgumentParser()
parser.add_argument('--address', default='localhost:50051')
args = parser.parse_args()


def outgoing():
    yield stream_pb2.ClientMessage(
        subscription = stream_pb2.SubscriptionRequest(
            type        = stream_pb2.ALL,
            vehicle_ids = [],
        ),
        metadata = common_pb2.FrontendMetadata(message_id='sub-001'),
    )
    # Keep the send stream open without sending more messages.
    while True:
        time.sleep(30)


with grpc.insecure_channel(args.address) as channel:
    stub = stream_pb2_grpc.ClientServiceStub(channel)
    print(f'Connected to {args.address}')
    try:
        for server_msg in stub.ClientStream(outgoing()):
            field = server_msg.WhichOneof('payload')
            print(f'[server -> client] {field}: {getattr(server_msg, field)}')
    except KeyboardInterrupt:
        pass
    except grpc.RpcError as e:
        print(f'RPC error: {e.details()}')
