import collections
import json
import logging
import os
import queue
import threading
import time
import traceback

import grpc
import rclpy
import yaml
from concurrent import futures
from rclpy.executors import MultiThreadedExecutor
from rclpy.node import Node
from rclpy.qos import DurabilityPolicy, HistoryPolicy, QoSProfile, ReliabilityPolicy

from .codec import (
    active_oneof_field,
    load_ros_type,
    make_ros_deserializer,
    make_ros_serializer,
    proto_field_set,
    proto_field_to_bytes,
    wire_ros_type,
)
from .proto_registry import FieldMapping, StreamDef, STREAMS
from .auth import make_channel
from .servicer_factory import build_servicer

_DURABILITY = {
    'volatile':        DurabilityPolicy.VOLATILE,
    'transient_local': DurabilityPolicy.TRANSIENT_LOCAL,
}
_RELIABILITY = {
    'best_effort': ReliabilityPolicy.BEST_EFFORT,
    'reliable':    ReliabilityPolicy.RELIABLE,
}


def _qos(cfg: dict, default_reliability: str = 'reliable') -> QoSProfile:
    return QoSProfile(
        depth=cfg.get('qos_depth', 10),
        durability=_DURABILITY.get(cfg.get('qos_durability', 'volatile'), DurabilityPolicy.VOLATILE),
        reliability=_RELIABILITY.get(cfg.get('qos_reliability', default_reliability),
                                     _RELIABILITY[default_reliability]),
        history=HistoryPolicy.KEEP_LAST,
    )


class ROS2GrpcBridge(Node):
    def __init__(self):
        super().__init__('grpc_bridge_node')
        self.declare_parameter('config_path', '')
        self.declare_parameter('grpc_host',   '0.0.0.0')
        self.declare_parameter('grpc_port',   50051)

        config_path = self.get_parameter('config_path').get_parameter_value().string_value
        if not config_path or not os.path.exists(config_path):
            self.get_logger().fatal(f'Config not found: {config_path}')
            return

        with open(config_path) as f:
            self.config = yaml.safe_load(f)

        self.ros_pubs:          dict  = {}
        self.ros_subs:          list  = []
        self.ros_publish_queue        = queue.Queue()
        self.stream_send_queues: dict = {}   # stream.key -> Queue[proto_msg]
        self._last_sent:         dict = {}   # stream.key -> {oneof_field: proto_msg}
        self.shutdown_event           = threading.Event()

        self._recv_counts  = collections.Counter()  # oneof field -> messages off the wire
        self._pub_counts   = collections.Counter()  # ros topic   -> messages published
        self._drop_counts  = collections.Counter()  # reason      -> messages discarded
        self._last_stats   = None

        self._grpc_server    = None
        self._grpc_channels: dict = {}

        from . import codec as _codec
        self.get_logger().info(f'codec module: {_codec.__file__}')

        self._setup_publishers()
        self._setup_grpc_server()
        self._setup_server_streams()
        self._setup_client_streams()
        self.create_timer(0.01, self._drain_publish_queue)
        self.create_timer(float(self.config.get('stats_interval', 5.0)), self._log_stats)

    # ------------------------------------------------------------------
    # Publisher setup
    # ------------------------------------------------------------------

    def _setup_publishers(self):
        """Pre-create ROS publishers for all recv_fields across enabled streams."""
        enabled = set(self.config.get('enabled_streams', list(STREAMS.keys())))

        for key, stream in STREAMS.items():
            if key not in enabled:
                continue
            for fm in stream.recv_fields:
                if fm.ros_topic in self.ros_pubs:
                    continue
                wire_type = wire_ros_type(fm.ros_msg_type, fm.format)
                ros_type  = load_ros_type(wire_type)
                self.ros_pubs[fm.ros_topic] = self.create_publisher(
                    ros_type, fm.ros_topic, _qos(self.config.get('qos', {}), 'reliable'))
                self.get_logger().info(f'Publisher: {fm.ros_topic}')

    # ------------------------------------------------------------------
    # gRPC server (bridge acts as server -- remote connects to us)
    # ------------------------------------------------------------------

    def _setup_grpc_server(self):
        host = self.get_parameter('grpc_host').get_parameter_value().string_value
        port = self.get_parameter('grpc_port').get_parameter_value().integer_value

        self._grpc_server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))

        server_streams = self.config.get('server_streams', [])
        for entry in server_streams:
            key    = entry['stream']
            stream = STREAMS.get(key)
            if stream is None:
                self.get_logger().error(f'Unknown stream: {key}')
                continue
            servicer = build_servicer(stream, self)
            stream.add_servicer_fn(servicer, self._grpc_server)
            self._setup_send_subscriptions(stream)
            self.get_logger().info(f'Server stream registered: {key}')

        addr = f'{host}:{port}'
        self._grpc_server.add_insecure_port(addr)
        self._grpc_server.start()
        self.get_logger().info(f'gRPC server listening on {addr}')

    # ------------------------------------------------------------------
    # Client streams (bridge dials out to a remote gRPC server)
    # ------------------------------------------------------------------

    def _setup_client_streams(self):
        for entry in self.config.get('client_streams', []):
            key         = entry['stream']
            remote_addr = entry.get('grpc_address') or os.environ.get('GRPC_ENDPOINT', '')
            if not remote_addr:
                self.get_logger().error(f'client_stream {key}: no grpc_address and GRPC_ENDPOINT not set')
                continue
            stream      = STREAMS.get(key)
            if stream is None:
                self.get_logger().error(f'Unknown stream: {key}')
                continue

            self._setup_send_subscriptions(stream)
            send_queue = self.stream_send_queues.setdefault(stream.key, queue.Queue())
            self._seed_initial_send(stream, entry)

            def _sender(sq=send_queue, shutdown=self.shutdown_event, s=stream):
                """Replay the last message per oneof field, then stream live ones until shutdown."""
                for msg in list(self._last_sent.get(s.key, {}).values()):
                    yield msg
                while not shutdown.is_set():
                    try:
                        msg = sq.get(timeout=0.5)
                        if msg is None:
                            return
                        self._last_sent.setdefault(s.key, {})[active_oneof_field(msg)] = msg
                        yield msg
                    except queue.Empty:
                        continue

            def _worker(addr=remote_addr, s=stream, sq=send_queue, sender=_sender):
                attempt = 0
                while not self.shutdown_event.is_set():
                    attempt += 1
                    gen = None
                    opened = time.monotonic()
                    count = 0
                    try:
                        # A stream torn down by the peer can leave the cached channel
                        # unusable, so every retry after the first gets a fresh one.
                        channel = self._channel(addr, reset=attempt > 1)
                        stub    = s.stub_cls(channel)
                        rpc     = getattr(stub, s.rpc)
                        seeded  = list(self._last_sent.get(s.key, {}))
                        self.get_logger().info(
                            f'[{s.key}] opening stream (attempt {attempt}), '
                            f'replaying {seeded or "nothing"}')

                        if s.stream_type == 'bidi':
                            gen = sender()
                            for recv_msg in rpc(gen):
                                count += 1
                                if count == 1:
                                    self.get_logger().info(
                                        f'[{s.key}] first message after '
                                        f'{time.monotonic() - opened:.1f}s')
                                self._dispatch_recv(s, recv_msg)

                        elif s.stream_type == 'server_streaming':
                            req = s.send_msg_cls()
                            for recv_msg in rpc(req):
                                count += 1
                                self._dispatch_recv(s, recv_msg)

                        elif s.stream_type == 'client_streaming':
                            gen = sender()
                            rpc(gen)

                        self.get_logger().warn(
                            f'[{s.key}] stream ended cleanly after '
                            f'{time.monotonic() - opened:.1f}s and {count} message(s), '
                            f'reconnecting in 2s')
                        time.sleep(2)

                    except grpc.RpcError as e:
                        self.get_logger().warn(
                            f'[{s.key}] {e.code().name} after '
                            f'{time.monotonic() - opened:.1f}s and {count} message(s): '
                            f'{e.details()} -- reconnecting in 2s')
                        time.sleep(2)
                    except Exception:
                        self.get_logger().error(f'[{s.key}] worker: {traceback.format_exc()}')
                        time.sleep(2)
                    finally:
                        # Without this the old generator stays parked on sq.get and
                        # competes with the next connection's sender for the queue.
                        if gen is not None:
                            gen.close()

            threading.Thread(target=_worker, daemon=True).start()
            self.get_logger().info(f'Client stream: {key} -> {remote_addr}')

    # ------------------------------------------------------------------
    # Initial send-direction messages
    # ------------------------------------------------------------------

    def _seed_initial_send(self, stream: StreamDef, entry: dict):
        """
        Prime _last_sent so the stream opens with these messages already queued.

        Send fields are normally driven by ROS publishers, which means a stream
        whose remote peer waits for a request (a subscription, a handshake) stays
        silent until something publishes. _sender replays _last_sent at the start
        of every connection, so seeding here also covers reconnects.
        """
        for item in entry.get('initial_send', []):
            field = item.get('field')
            fm    = stream.send_field_map.get(field)
            if fm is None:
                self.get_logger().error(
                    f'[{stream.key}] initial_send: unknown send field {field!r}')
                continue

            payload = item.get('payload', {})
            if not payload:
                self.get_logger().error(
                    f'[{stream.key}] initial_send {field}: empty payload leaves the '
                    f'oneof unset, the peer will not see this message')
                continue

            try:
                msg = proto_field_set(
                    stream.send_msg_cls, field, json.dumps(payload).encode(), fm.format)
            except Exception as e:
                self.get_logger().error(f'[{stream.key}] initial_send {field}: {e}')
                continue

            if active_oneof_field(msg) != field:
                self.get_logger().error(
                    f'[{stream.key}] initial_send {field}: oneof did not take')
                continue

            self._last_sent.setdefault(stream.key, {})[field] = msg
            self.get_logger().info(f'[{stream.key}] initial send: {field} {payload}')

    # ------------------------------------------------------------------
    # Server streams (identical to client but called from _setup_grpc_server)
    # ------------------------------------------------------------------

    def _setup_server_streams(self):
        """Server-mode streams also need their send-direction ROS subscriptions."""
        # Already handled inside _setup_grpc_server per entry.
        pass

    # ------------------------------------------------------------------
    # Shared: subscribe to ROS topics that feed into a stream's send direction
    # ------------------------------------------------------------------

    def _setup_send_subscriptions(self, stream: StreamDef):
        for fm in stream.send_fields:
            if any(s.topic_name == fm.ros_topic for s in self.ros_subs):
                continue  # already subscribed

            wire_type = wire_ros_type(fm.ros_msg_type, fm.format)
            ros_type  = load_ros_type(wire_type)
            serialize = make_ros_serializer(wire_type, fm.format)
            send_queue = self.stream_send_queues.setdefault(stream.key, queue.Queue())

            def cb(ros_msg, f=fm, cls=stream.send_msg_cls, sq=send_queue, ser=serialize):
                try:
                    payload   = ser(ros_msg)
                    proto_msg = proto_field_set(cls, f.field_name, payload, f.format)
                    sq.put(proto_msg)
                except Exception as e:
                    self.get_logger().error(
                        f'[{stream.key}] pack {f.field_name}: {e}')

            sub = self.create_subscription(ros_type, fm.ros_topic, cb,
                                          _qos(self.config.get('qos', {}), 'reliable'))
            self.ros_subs.append(sub)
            self.get_logger().info(f'Send sub: {fm.ros_topic} -> {stream.key}.{fm.field_name}')

    # ------------------------------------------------------------------
    # Receive dispatch (used by client-mode streams)
    # ------------------------------------------------------------------

    def _dispatch_recv(self, stream: StreamDef, proto_msg):
        field_name = active_oneof_field(proto_msg)
        self._recv_counts[field_name or '<no payload set>'] += 1

        fm = stream.recv_field_map.get(field_name)
        if fm is None:
            self._drop_counts[f'no recv_fields entry: {field_name or "<unset oneof>"}'] += 1
            return

        payload = proto_field_to_bytes(proto_msg, field_name, fm.format)
        if payload is None:
            self._drop_counts[f'encode returned None: {field_name}'] += 1
            return

        wire_type   = wire_ros_type(fm.ros_msg_type, fm.format)
        ros_type    = load_ros_type(wire_type)
        deserialize = make_ros_deserializer(ros_type, fm.format)

        try:
            ros_msg = deserialize(payload)
        except Exception as e:
            self._drop_counts[f'deserialize failed: {field_name}'] += 1
            self.get_logger().error(f'[{stream.key}] deser {field_name}: {e}')
            return

        pub = self.ros_pubs.get(fm.ros_topic)
        if pub is None:
            self._drop_counts[f'no publisher: {fm.ros_topic}'] += 1
            self.get_logger().warn(f'[{stream.key}] no publisher for {fm.ros_topic}')
            return

        self.ros_publish_queue.put((pub, ros_msg))

    def _log_stats(self):
        state = (dict(self._recv_counts), dict(self._pub_counts), dict(self._drop_counts))
        if state == self._last_stats:
            return
        self._last_stats = state

        fmt = lambda c: ', '.join(f'{k}={v}' for k, v in sorted(c.items())) or 'none'
        self.get_logger().info(f'grpc recv: {fmt(self._recv_counts)}')
        self.get_logger().info(f'ros  pub:  {fmt(self._pub_counts)}')
        if self._drop_counts:
            self.get_logger().warn(f'dropped:   {fmt(self._drop_counts)}')

    # ------------------------------------------------------------------

    def _channel(self, address: str, reset: bool = False) -> grpc.Channel:
        if reset and address in self._grpc_channels:
            try:
                self._grpc_channels.pop(address).close()
            except Exception:
                pass
        if address not in self._grpc_channels:
            self._grpc_channels[address] = make_channel(address)
        return self._grpc_channels[address]

    def _drain_publish_queue(self):
        while not self.ros_publish_queue.empty():
            pub, msg = self.ros_publish_queue.get_nowait()
            pub.publish(msg)
            self._pub_counts[pub.topic_name] += 1

    def shutdown(self):
        self.shutdown_event.set()
        for sq in self.stream_send_queues.values():
            sq.put(None)
        if self._grpc_server:
            self._grpc_server.stop(grace=2)
        for ch in self._grpc_channels.values():
            ch.close()


def main(args=None):
    logging.basicConfig(level=logging.INFO, format='[auth] %(levelname)s %(message)s')
    rclpy.init(args=args)
    node = ROS2GrpcBridge()
    executor = MultiThreadedExecutor()
    executor.add_node(node)
    try:
        executor.spin()
    except KeyboardInterrupt:
        pass
    finally:
        node.shutdown()
        executor.shutdown()
        node.destroy_node()
        rclpy.shutdown()
