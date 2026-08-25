#!/usr/bin/env python3
"""
Simulates a vehicle connecting to the bridge as a gRPC client.

Streams VehicleMessage telemetry/heartbeat to the bridge and prints any
ServerMessage commands it receives back.

Usage:
    python3 scripts/test_vehicle_client.py [--address localhost:50051]
"""
import argparse
import sys
import time
import threading
import os

# Add generated stubs to path.
_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, '..', 'proto', 'generated'))

import grpc
from vehicle import stream_pb2, stream_pb2_grpc
from messages import telemetry_pb2, events_pb2, common_pb2

parser = argparse.ArgumentParser()
parser.add_argument('--address', default='localhost:50051')
parser.add_argument('--interval', type=float, default=1.0, help='Telemetry publish interval (s)')
args = parser.parse_args()


def message_stream():
    seq = 0
    while True:
        telemetry = telemetry_pb2.Telemetry(
            state    = common_pb2.NOMINAL_DRIVING,
            heading  = 1.57,
            velocity = 30.0,
            battery  = 87.5,
            passengers = 2,
        )
        yield stream_pb2.VehicleMessage(
            telemetry = telemetry,
            metadata  = common_pb2.MessageMetadata(
                message_id = f'msg-{seq}',
                vehicle_id = 'vehicle-001',
            ),
        )

        if seq % 5 == 0:
            yield stream_pb2.VehicleMessage(
                heartbeat = events_pb2.Heartbeat(status='ok'),
                metadata  = common_pb2.MessageMetadata(vehicle_id='vehicle-001'),
            )

        seq += 1
        time.sleep(args.interval)


with grpc.insecure_channel(args.address) as channel:
    stub = stream_pb2_grpc.VehicleServiceStub(channel)
    print(f'Connected to {args.address}')
    try:
        for server_msg in stub.VehicleStream(message_stream()):
            field = server_msg.WhichOneof('payload')
            print(f'[server -> vehicle] {field}: {getattr(server_msg, field)}')
    except KeyboardInterrupt:
        pass
    except grpc.RpcError as e:
        print(f'RPC error: {e.details()}')
