"""Test client: subscribes to a topic stream from a running grpc_message_bridge server."""
import argparse
import grpc
from grpc_message_bridge import ros_bridge_pb2, ros_bridge_pb2_grpc

parser = argparse.ArgumentParser()
parser.add_argument('--address', default='localhost:50051')
parser.add_argument('--topic',   default='/ros2_chatter')
parser.add_argument('--count',   type=int, default=0, help='0 = infinite')
args = parser.parse_args()

with grpc.insecure_channel(args.address) as channel:
    stub = ros_bridge_pb2_grpc.RosBridgeStub(channel)
    req  = ros_bridge_pb2.SubscribeRequest(
        topic    = args.topic,
        ros_type = 'std_msgs/msg/String',
        format   = 'cdr',
    )
    received = 0
    for msg in stub.Subscribe(req):
        print(f'[{msg.topic}] seq={msg.seq} payload={msg.payload!r}')
        received += 1
        if args.count and received >= args.count:
            break
