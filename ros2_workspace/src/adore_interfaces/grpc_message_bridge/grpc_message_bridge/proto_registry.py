"""
Typed registry of gRPC streams and their ROS topic mappings.

The bridge is a CLIENT that dials supervision.dev-motor-ai.com:443.

ClientStream directions:
  send (ClientMessage)  -- bridge -> server: subscription requests, acks, signaling
  recv (ServerMessage)  -- server -> bridge: telemetry updates, notifications, acks

Adding a new stream:
  1. Add .proto files under proto/ and run `make gen_proto`.
  2. Define a StreamDef below and add it to STREAMS.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Type


from client import stream_pb2       as client_stream_pb2
from client import stream_pb2_grpc  as client_stream_grpc


@dataclass
class FieldMapping:
    field_name:   str
    ros_topic:    str
    ros_msg_type: str  = 'std_msgs/msg/String'
    format:       str  = 'json'


@dataclass
class StreamDef:
    service_name:    str
    rpc:             str
    stream_type:     str          # bidi | client_streaming | server_streaming
    send_msg_cls:    Type[Any]    # proto class the bridge sends to the server
    recv_msg_cls:    Type[Any]    # proto class the bridge receives from the server
    stub_cls:        Type[Any]
    add_servicer_fn: Any
    servicer_base:   Type[Any]
    send_fields:     List[FieldMapping] = field(default_factory=list)
    recv_fields:     List[FieldMapping] = field(default_factory=list)

    @property
    def key(self) -> str:
        return f'{self.service_name}.{self.rpc}'

    @property
    def recv_field_map(self) -> Dict[str, FieldMapping]:
        return {f.field_name: f for f in self.recv_fields}

    @property
    def send_field_map(self) -> Dict[str, FieldMapping]:
        return {f.field_name: f for f in self.send_fields}


CLIENT_STREAM = StreamDef(
    service_name    = 'client.ClientService',
    rpc             = 'ClientStream',
    stream_type     = 'bidi',

    # Bridge sends ClientMessage to server
    send_msg_cls    = client_stream_pb2.ClientMessage,
    # Bridge receives ServerMessage from server
    recv_msg_cls    = client_stream_pb2.ServerMessage,

    stub_cls        = client_stream_grpc.ClientServiceStub,
    add_servicer_fn = client_stream_grpc.add_ClientServiceServicer_to_server,
    servicer_base   = client_stream_grpc.ClientServiceServicer,

    # What we send to the server (ClientMessage oneofs)
    send_fields=[
        FieldMapping('subscription',  '/supervision/subscription',  'std_msgs/msg/String', 'json'),
        FieldMapping('ack',           '/supervision/ack/tx',        'std_msgs/msg/String', 'json'),
        FieldMapping('signal_message','/supervision/signaling/tx',  'std_msgs/msg/String', 'json'),
    ],

    # What we receive from the server (ServerMessage oneofs) -> ROS topics
    recv_fields=[
        FieldMapping('telemetry',     '/supervision/telemetry',     'std_msgs/msg/String', 'json'),
        FieldMapping('notification',  '/supervision/notifications', 'std_msgs/msg/String', 'json'),
        FieldMapping('ack',           '/supervision/ack/rx',        'std_msgs/msg/String', 'json'),
        FieldMapping('signal_message','/supervision/signaling/rx',  'std_msgs/msg/String', 'json'),
    ],
)

STREAMS: Dict[str, StreamDef] = {
    CLIENT_STREAM.key: CLIENT_STREAM,
}
