import os
import queue
import threading
import time
import yaml
import grpc
import rclpy
from concurrent import futures
from rclpy.node import Node
from rclpy.executors import MultiThreadedExecutor
from rclpy.qos import QoSProfile, DurabilityPolicy, ReliabilityPolicy, HistoryPolicy
from . import ros_bridge_pb2, ros_bridge_pb2_grpc
from .utils import load_msg_type, msg_to_bytes, bytes_to_msg, msg_to_json, json_to_msg, msg_to_cdr_json, cdr_json_to_msg

_STR_TYPE = 'std_msgs/msg/String'

_DURABILITY = {
    'volatile':        DurabilityPolicy.VOLATILE,
    'transient_local': DurabilityPolicy.TRANSIENT_LOCAL,
}
_RELIABILITY = {
    'best_effort': ReliabilityPolicy.BEST_EFFORT,
    'reliable':    ReliabilityPolicy.RELIABLE,
}


def _wire_type(ros_type: str, fmt: str) -> str:
    return _STR_TYPE if fmt in ('json', 'cdr_json') else ros_type


def _serializer(ros_type: str, fmt: str):
    if fmt == 'json':
        return lambda msg, rt=ros_type: msg_to_json(msg, rt)
    if fmt == 'cdr_json':
        return lambda msg, rt=ros_type: msg_to_cdr_json(msg, rt)
    return msg_to_bytes


def _deserializer(msg_type, fmt: str):
    if fmt == 'json':
        return lambda data, mt=msg_type: json_to_msg(data, mt)
    if fmt == 'cdr_json':
        return lambda data, mt=msg_type: cdr_json_to_msg(data, mt)
    return lambda data, mt=msg_type: bytes_to_msg(data, mt)


def _qos_from_mapping(mapping: dict, default_reliability: str = 'reliable') -> QoSProfile:
    return QoSProfile(
        depth=mapping.get('qos_depth', 1),
        durability=_DURABILITY.get(mapping.get('qos_durability', 'volatile'), DurabilityPolicy.VOLATILE),
        reliability=_RELIABILITY.get(mapping.get('qos_reliability', default_reliability),
                                     _RELIABILITY[default_reliability]),
        history=HistoryPolicy.KEEP_LAST,
    )


class RosBridgeServicer(ros_bridge_pb2_grpc.RosBridgeServicer):
    """gRPC servicer: handles inbound Publish streams and outbound Subscribe streams."""

    def __init__(self, node: 'ROS2GrpcBridge'):
        self._node = node

    def Publish(self, request_iterator, context):
        """Receive a stream of RosMessages from a remote publisher and forward to ROS."""
        for grpc_msg in request_iterator:
            if self._node._shutdown_event.is_set():
                break
            topic = grpc_msg.topic
            pub   = self._node.ros_pubs.get(topic)
            if pub is None:
                self._node.get_logger().warn(f'Received publish for unconfigured topic: {topic}')
                continue
            deser = self._node._grpc_deserializers.get(topic)
            if deser is None:
                continue
            try:
                msg = deser(grpc_msg.payload)
                self._node._grpc_to_ros_queue.put((pub, msg))
            except Exception as e:
                self._node.get_logger().error(f'Deser failed on {topic}: {e}')
        return ros_bridge_pb2.Ack(ok=True)

    def Subscribe(self, request, context):
        """Stream RosMessages to a remote subscriber for a configured topic."""
        topic = request.topic
        sub_queue = queue.Queue()

        with self._node._subscriber_lock:
            self._node._grpc_subscribers.setdefault(topic, []).append(sub_queue)

        self._node.get_logger().info(f'gRPC subscriber connected: {topic}')
        try:
            while not self._node._shutdown_event.is_set() and context.is_active():
                try:
                    grpc_msg = sub_queue.get(timeout=0.1)
                    yield grpc_msg
                except queue.Empty:
                    continue
        finally:
            with self._node._subscriber_lock:
                subs = self._node._grpc_subscribers.get(topic, [])
                if sub_queue in subs:
                    subs.remove(sub_queue)
            self._node.get_logger().info(f'gRPC subscriber disconnected: {topic}')


class ROS2GrpcBridge(Node):
    def __init__(self):
        super().__init__('grpc_bridge_node')
        self.declare_parameter('config_path', '')
        self.declare_parameter('grpc_host', '0.0.0.0')
        self.declare_parameter('grpc_port', 50051)
        self.declare_parameter('grpc_server_address', '')

        config_path = self.get_parameter('config_path').get_parameter_value().string_value
        if not config_path or not os.path.exists(config_path):
            self.get_logger().error(f'Config file not found: {config_path}')
            return

        try:
            with open(config_path, 'r') as f:
                self.config = yaml.safe_load(f)
        except Exception as e:
            self.get_logger().error(f'Failed to load config: {e}')
            return

        self.ros_subs  = []
        self.ros_pubs  = {}
        self._grpc_deserializers    = {}
        self._grpc_to_ros_queue     = queue.Queue()
        self._grpc_subscribers      = {}
        self._subscriber_lock       = threading.Lock()
        self._shutdown_event        = threading.Event()
        self._grpc_clients          = {}
        self._grpc_channels         = {}
        self._grpc_pub_streams      = {}

        self._setup_grpc_server()
        self._setup_ros2_to_grpc()
        self._setup_grpc_to_ros2()
        self.create_timer(0.01, self._drain_grpc_to_ros_queue)

    def _setup_grpc_server(self):
        host = self.get_parameter('grpc_host').get_parameter_value().string_value
        port = self.get_parameter('grpc_port').get_parameter_value().integer_value
        self._grpc_server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        ros_bridge_pb2_grpc.add_RosBridgeServicer_to_server(RosBridgeServicer(self), self._grpc_server)
        listen_addr = f'{host}:{port}'
        self._grpc_server.add_insecure_port(listen_addr)
        self._grpc_server.start()
        self.get_logger().info(f'gRPC server listening on {listen_addr}')

    def _get_client(self, address: str):
        if address not in self._grpc_channels:
            channel = grpc.insecure_channel(address)
            self._grpc_channels[address] = channel
            self._grpc_clients[address]  = ros_bridge_pb2_grpc.RosBridgeStub(channel)
        return self._grpc_clients[address]

    def _setup_ros2_to_grpc(self):
        """Subscribe to ROS topics and stream messages to remote gRPC servers."""
        for mapping in self.config.get('ros2_to_grpc', []):
            ros_topic   = mapping['ros_topic']
            ros_type    = mapping.get('msg_type', _STR_TYPE)
            remote_addr = mapping.get('grpc_address', '')
            fmt         = mapping.get('format', 'cdr')
            qos         = _qos_from_mapping(mapping, default_reliability='reliable')
            msg_type    = load_msg_type(ros_type)
            serialize   = _serializer(ros_type, fmt)
            seq         = [0]

            if not remote_addr:
                self.get_logger().error(f'ros2_to_grpc entry for {ros_topic} missing grpc_address')
                continue

            # Stream queue feeding a persistent per-topic publisher thread.
            stream_queue: queue.Queue = queue.Queue()
            self._grpc_pub_streams[ros_topic] = stream_queue

            def _stream_worker(addr=remote_addr, topic=ros_topic, rtype=ros_type, f=fmt, sq=stream_queue):
                while not self._shutdown_event.is_set():
                    try:
                        stub = self._get_client(addr)
                        stub.Publish(iter(sq.get, None))
                    except grpc.RpcError as e:
                        self.get_logger().warn(f'gRPC publish error on {topic}: {e.details()} -- retrying in 2s')
                        time.sleep(2)

            t = threading.Thread(target=_stream_worker, daemon=True)
            t.start()

            self.get_logger().info(f'R2G: {ros_topic} -> {remote_addr} [{fmt}]')

            def cb(msg, sq=stream_queue, topic=ros_topic, rtype=ros_type, f=fmt, s=seq, ser=serialize):
                grpc_msg = ros_bridge_pb2.RosMessage(
                    topic    = topic,
                    ros_type = rtype,
                    format   = f,
                    payload  = ser(msg),
                    seq      = s[0],
                    stamp_ns = time.time_ns(),
                )
                s[0] += 1
                sq.put(grpc_msg)
                self.get_logger().debug(f'R2G queued: {topic}')

            self.ros_subs.append(self.create_subscription(msg_type, ros_topic, cb, qos))

    def _setup_grpc_to_ros2(self):
        """For each grpc_to_ros2 entry, register a ROS publisher and accept inbound gRPC Publish calls."""
        for mapping in self.config.get('grpc_to_ros2', []):
            ros_topic = mapping['ros_topic']
            ros_type  = mapping.get('msg_type', _STR_TYPE)
            fmt       = mapping.get('format', 'cdr')
            wtype     = _wire_type(ros_type, fmt)
            qos       = _qos_from_mapping(mapping, default_reliability='best_effort')
            pub_type  = load_msg_type(wtype)
            m_type    = load_msg_type(ros_type)

            self.ros_pubs[ros_topic]             = self.create_publisher(pub_type, ros_topic, qos)
            self._grpc_deserializers[ros_topic]  = _deserializer(m_type, fmt)
            self.get_logger().info(f'G2R: registered inbound topic {ros_topic} [{fmt}]')

    def _setup_grpc_subscribe_forwarders(self):
        """
        For ros2_to_grpc entries that also want a remote Subscribe channel,
        connect as a gRPC client subscriber and publish received messages locally.
        Used when the remote side is a server and this node is the consumer.
        """
        for mapping in self.config.get('grpc_subscribe_from', []):
            ros_topic   = mapping['ros_topic']
            ros_type    = mapping.get('msg_type', _STR_TYPE)
            remote_addr = mapping['grpc_address']
            fmt         = mapping.get('format', 'cdr')
            qos         = _qos_from_mapping(mapping, default_reliability='best_effort')
            wtype       = _wire_type(ros_type, fmt)
            pub_type    = load_msg_type(wtype)
            m_type      = load_msg_type(ros_type)
            deserialize = _deserializer(m_type, fmt)

            pub = self.create_publisher(pub_type, ros_topic, qos)
            self.ros_pubs[ros_topic] = pub
            self.get_logger().info(f'GSF: {remote_addr} -> {ros_topic} [{fmt}]')

            def _sub_worker(addr=remote_addr, topic=ros_topic, rtype=ros_type, f=fmt, p=pub, deser=deserialize):
                while not self._shutdown_event.is_set():
                    try:
                        stub = self._get_client(addr)
                        req  = ros_bridge_pb2.SubscribeRequest(topic=topic, ros_type=rtype, format=f)
                        for grpc_msg in stub.Subscribe(req):
                            if self._shutdown_event.is_set():
                                break
                            try:
                                msg = deser(grpc_msg.payload)
                                self._grpc_to_ros_queue.put((p, msg))
                            except Exception as e:
                                self.get_logger().error(f'Deser failed on {topic}: {e}')
                    except grpc.RpcError as e:
                        self.get_logger().warn(f'gRPC subscribe error on {topic}: {e.details()} -- retrying in 2s')
                        time.sleep(2)

            threading.Thread(target=_sub_worker, daemon=True).start()

    def _drain_grpc_to_ros_queue(self):
        while not self._grpc_to_ros_queue.empty():
            pub, msg = self._grpc_to_ros_queue.get_nowait()
            pub.publish(msg)

    def shutdown(self):
        self._shutdown_event.set()
        # Sentinel None unblocks iter(queue.get, None) in publisher threads.
        for sq in self._grpc_pub_streams.values():
            sq.put(None)
        self._grpc_server.stop(grace=2)
        for ch in self._grpc_channels.values():
            ch.close()


def main(args=None):
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
