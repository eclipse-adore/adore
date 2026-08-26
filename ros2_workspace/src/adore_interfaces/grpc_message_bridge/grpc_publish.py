"""Test client: streams RosMessages to a running grpc_message_bridge server."""
import argparse
import grpc
import json
import time
from grpc_message_bridge import ros_bridge_pb2, ros_bridge_pb2_grpc

parser = argparse.ArgumentParser()
parser.add_argument('--address', default='localhost:50051')
parser.add_argument('--topic',   default='/grpc_chatter')
parser.add_argument('--count',   type=int, default=0, help='0 = infinite')
args = parser.parse_args()

def message_stream():
    seq = 0
    while args.count == 0 or seq < args.count:
        payload = json.dumps({'data': f'Hello gRPC #{seq}'}).encode()
        yield ros_bridge_pb2.RosMessage(
            topic    = args.topic,
            ros_type = 'std_msgs/msg/String',
            format   = 'json',
            payload  = payload,
            seq      = seq,
            stamp_ns = time.time_ns(),
        )
        print(f'Published seq={seq}')
        seq += 1
        if args.count == 0:
            time.sleep(1)

with grpc.insecure_channel(args.address) as channel:
    stub = ros_bridge_pb2_grpc.RosBridgeStub(channel)
    ack  = stub.Publish(message_stream())
    print(f'Ack: {ack}')
