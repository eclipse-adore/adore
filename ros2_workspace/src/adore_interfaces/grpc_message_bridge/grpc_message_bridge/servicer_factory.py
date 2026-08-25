"""
Builds gRPC servicer classes at runtime from StreamDef descriptors.

Each servicer handles one RPC method. On every incoming proto message it:
  1. Identifies the active oneof field.
  2. Looks it up in the StreamDef's recv_field_map.
  3. Deserializes the field value to a ROS message and puts it on the ROS publish queue.
  4. For bidi/server-streaming: yields any queued outbound proto messages.
"""

import queue
import threading
from typing import TYPE_CHECKING

from .codec import (
    active_oneof_field,
    load_ros_type,
    make_ros_deserializer,
    proto_field_to_bytes,
    wire_ros_type,
)
from .proto_registry import FieldMapping, StreamDef

if TYPE_CHECKING:
    from .bridge_node import ROS2GrpcBridge


def build_servicer(stream: StreamDef, node: 'ROS2GrpcBridge'):
    """
    Return a fully-wired servicer instance for stream.rpc.

    The servicer class is created dynamically so we can close over node and
    stream without requiring a fixed class hierarchy.
    """
    send_queue = node.stream_send_queues.setdefault(stream.key, queue.Queue())

    def _handle_recv(proto_msg):
        field_name = active_oneof_field(proto_msg)
        mapping    = stream.recv_field_map.get(field_name)
        if mapping is None:
            return

        payload = proto_field_to_bytes(proto_msg, field_name, mapping.format)
        if payload is None:
            return

        wire_type  = wire_ros_type(mapping.ros_msg_type, mapping.format)
        ros_type   = load_ros_type(wire_type)
        deserialize = make_ros_deserializer(ros_type, mapping.format)

        try:
            ros_msg = deserialize(payload)
        except Exception as e:
            node.get_logger().error(f'[{stream.key}] deserialize {field_name}: {e}')
            return

        pub = node.ros_pubs.get(mapping.ros_topic)
        if pub:
            node.ros_publish_queue.put((pub, ros_msg))
        else:
            node.get_logger().warn(f'[{stream.key}] no publisher for {mapping.ros_topic}')

    rpc_name = stream.rpc

    if stream.stream_type == 'bidi':
        def _bidi_rpc(self_svc, request_iterator, context):
            for proto_msg in request_iterator:
                if node.shutdown_event.is_set():
                    break
                _handle_recv(proto_msg)
                # Drain any queued outbound messages without blocking.
                while True:
                    try:
                        yield send_queue.get_nowait()
                    except queue.Empty:
                        break
        methods = {rpc_name: _bidi_rpc}

    elif stream.stream_type == 'client_streaming':
        def _client_stream_rpc(self_svc, request_iterator, context):
            for proto_msg in request_iterator:
                if node.shutdown_event.is_set():
                    break
                _handle_recv(proto_msg)
            return stream.send_msg_cls()
        methods = {rpc_name: _client_stream_rpc}

    else:  # server_streaming
        def _server_stream_rpc(self_svc, request, context):
            _handle_recv(request)
            while not node.shutdown_event.is_set() and context.is_active():
                try:
                    yield send_queue.get(timeout=0.1)
                except queue.Empty:
                    continue
        methods = {rpc_name: _server_stream_rpc}

    servicer_cls = type(f'{rpc_name}Servicer', (stream.servicer_base,), methods)
    return servicer_cls()
