import os
import queue
import threading
import yaml
import paho.mqtt.client as mqtt
import rclpy
from rclpy.node import Node
from rclpy.executors import MultiThreadedExecutor
from rclpy.qos import QoSProfile, DurabilityPolicy, ReliabilityPolicy, HistoryPolicy
from .utils import load_msg_type, msg_to_bytes, bytes_to_msg, msg_to_json, json_to_msg, msg_to_cdr_json, cdr_json_to_msg

_STR_TYPE = 'std_msgs/msg/String'

_PROTOCOL_MAP = {
    'mqtt':   mqtt.MQTTv311,
    'mqttv5': mqtt.MQTTv5,
}

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

def _wire_type(ros_type: str, fmt: str) -> str:
    return _STR_TYPE if fmt in ('json', 'cdr_json') else ros_type

_DURABILITY = {
    'volatile':        DurabilityPolicy.VOLATILE,
    'transient_local': DurabilityPolicy.TRANSIENT_LOCAL,
}
_RELIABILITY = {
    'best_effort': ReliabilityPolicy.BEST_EFFORT,
    'reliable':    ReliabilityPolicy.RELIABLE,
}

def _qos_from_mapping(mapping: dict) -> QoSProfile:
    return QoSProfile(
        depth=mapping.get('qos_depth', 10),
        durability=_DURABILITY.get(mapping.get('qos_durability', 'volatile'), DurabilityPolicy.VOLATILE),
        reliability=_RELIABILITY.get(mapping.get('qos_reliability', 'best_effort'), ReliabilityPolicy.BEST_EFFORT),
        history=HistoryPolicy.KEEP_LAST,
    )


class ROS2MQTTBridge(Node):
    def __init__(self):
        super().__init__('mqtt_bridge_node')
        self.declare_parameter('config_path', '')

        config_path = self.get_parameter('config_path').get_parameter_value().string_value
        if not config_path or not os.path.exists(config_path):
            self.get_logger().error(f"Config file not found: {config_path}")
            return

        try:
            with open(config_path, 'r') as f:
                self.config = yaml.safe_load(f)
        except Exception as e:
            self.get_logger().error(f"Failed to load config: {e}")
            return

        self.mqtt_client = None
        self.ros_subs = []
        self.ros_pubs = {}
        self._m2r_queue = queue.Queue()
        self._shutdown_event = threading.Event()
        self._mqtt_topic_map = {}

        self._load_env_file(self.config.get('mqtt', {}).get('env_file'))
        self._setup_mqtt()
        self._setup_ros2_to_mqtt()
        self._setup_mqtt_to_ros2()
        self.mqtt_client.loop_start()
        self.create_timer(0.01, self._drain_m2r_queue)

    def _load_env_file(self, env_file: str | None):
        if not env_file:
            return
        if not os.path.exists(env_file):
            self.get_logger().warning(f"env_file not found: {env_file}")
            return
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#') or '=' not in line:
                    continue
                key, _, value = line.partition('=')
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                os.environ.setdefault(key, value)
        self.get_logger().info(f"Loaded env file: {env_file}")

    @staticmethod
    def _env_or(cfg: dict, key: str, default=None):
        env_var = cfg.get(f'{key}_env')
        if env_var:
            val = os.environ.get(env_var)
            if val is not None:
                return val
        return cfg.get(key, default)

    def _setup_mqtt(self):
        cfg = self.config.get('mqtt', {})

        host      = self._env_or(cfg, 'host', 'localhost')
        port      = int(self._env_or(cfg, 'port', 1883))
        keepalive = int(self._env_or(cfg, 'keepalive', 60))
        transport = self._env_or(cfg, 'transport', 'tcp')
        protocol  = _PROTOCOL_MAP.get(self._env_or(cfg, 'protocol', 'mqtt'), mqtt.MQTTv311)

        self.mqtt_client = mqtt.Client(
            mqtt.CallbackAPIVersion.VERSION2,
            protocol=protocol,
            transport=transport,
        )
        self.mqtt_client.on_connect = self._on_mqtt_connect
        self.mqtt_client.on_message = self._on_mqtt_message

        self._configure_auth(cfg)
        self._configure_tls(cfg)
        self._configure_reconnect(cfg)

        self.mqtt_client.connect(host, port, keepalive=keepalive)
        self.get_logger().info(f'Connecting to MQTT broker: {host}:{port}')

    def _configure_auth(self, cfg: dict):
        auth = cfg.get('auth')
        if not auth:
            return

        username_env = auth.get('username_env')
        password_env = auth.get('password_env')

        username = os.environ.get(username_env) if username_env else None
        password = os.environ.get(password_env) if password_env else None

        if not username:
            self.get_logger().warning(
                f"MQTT auth enabled but env var '{username_env}' is not set or empty"
            )
            return

        self.mqtt_client.username_pw_set(username, password)
        self.get_logger().info(f"MQTT auth configured from env vars (user: '{username_env}')")

    def _configure_tls(self, cfg: dict):
        tls = cfg.get('tls')
        if not tls:
            return

        self.mqtt_client.tls_set(
            ca_certs=tls.get('ca_certs'),
            certfile=tls.get('certfile'),
            keyfile=tls.get('keyfile'),
        )
        if tls.get('insecure', False):
            self.mqtt_client.tls_insecure_set(True)
            self.get_logger().warning('TLS certificate verification is disabled')

    def _configure_reconnect(self, cfg: dict):
        delay     = self._env_or(cfg, 'reconnect_delay')
        max_delay = self._env_or(cfg, 'reconnect_max_delay')
        if delay is not None or max_delay is not None:
            self.mqtt_client.reconnect_delay_set(
                min_delay=int(delay or 1),
                max_delay=int(max_delay or 120),
            )

    def _on_mqtt_connect(self, client, userdata, flags, reason_code, properties):
        if reason_code == 0:
            self.get_logger().info('Connected to MQTT broker')
            for mqtt_topic in self._mqtt_topic_map:
                client.subscribe(mqtt_topic)
                self.get_logger().info(f'Subscribed to MQTT topic: {mqtt_topic}')
        else:
            self.get_logger().error(f'MQTT connection failed with code: {reason_code}')

    def _on_mqtt_message(self, client, userdata, message):
        if self._shutdown_event.is_set():
            return
        entry = self._mqtt_topic_map.get(message.topic)
        if entry is None:
            return
        pub, msg_type, ros_topic, deserialize = entry
        try:
            self._m2r_queue.put((pub, deserialize(message.payload)))
        except Exception as e:
            self.get_logger().error(f'Deser failed on {ros_topic}: {e}')

    def _setup_ros2_to_mqtt(self):
        for mapping in self.config.get('ros2_to_mqtt', []):
            ros_topic  = mapping['ros_topic']
            mqtt_topic = mapping['mqtt_topic']
            ros_type   = mapping.get('msg_type', _STR_TYPE)
            msg_type   = load_msg_type(ros_type)
            fmt        = mapping.get('format', 'cdr')
            qos        = _qos_from_mapping(mapping)
            serialize  = _serializer(ros_type, fmt)
            cb = lambda msg, t=mqtt_topic, s=serialize: (
                self.mqtt_client.publish(t, s(msg)),
                self.get_logger().debug(f'R2M: {t}')
            )
            self.ros_subs.append(self.create_subscription(msg_type, ros_topic, cb, qos))

    def _setup_mqtt_to_ros2(self):
        for mapping in self.config.get('mqtt_to_ros2', []):
            mqtt_topic  = mapping['mqtt_topic']
            ros_topic   = mapping['ros_topic']
            ros_type    = mapping.get('msg_type', _STR_TYPE)
            fmt         = mapping.get('format', 'cdr')
            pub_type    = load_msg_type(_wire_type(ros_type, fmt))
            m_type      = load_msg_type(ros_type)
            qos         = _qos_from_mapping(mapping)
            pub         = self.create_publisher(pub_type, ros_topic, qos)
            deserialize = _deserializer(m_type, fmt)
            self.ros_pubs[mqtt_topic] = pub
            self._mqtt_topic_map[mqtt_topic] = (pub, m_type, ros_topic, deserialize)

        if self.mqtt_client.is_connected():
            for mqtt_topic in self._mqtt_topic_map:
                self.mqtt_client.subscribe(mqtt_topic)

    def _drain_m2r_queue(self):
        while not self._m2r_queue.empty():
            pub, msg = self._m2r_queue.get_nowait()
            pub.publish(msg)

    def shutdown(self):
        self._shutdown_event.set()
        self.mqtt_client.loop_stop()
        self.mqtt_client.disconnect()


def main(args=None):
    rclpy.init(args=args)
    node = ROS2MQTTBridge()
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
