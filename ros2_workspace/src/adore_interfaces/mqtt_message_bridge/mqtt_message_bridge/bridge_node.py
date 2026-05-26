import os
import queue
import threading
import yaml
import paho.mqtt.client as mqtt
import rclpy
from rclpy.node import Node
from rclpy.executors import MultiThreadedExecutor
from rclpy.qos import QoSProfile, DurabilityPolicy, ReliabilityPolicy, HistoryPolicy
from .utils import load_msg_type, msg_to_bytes, bytes_to_msg, msg_to_json, json_to_msg

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
        self.declare_parameter('mqtt_broker', 'localhost')
        self.declare_parameter('mqtt_port', 1883)

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

        # Map MQTT topic -> (ros_publisher, msg_type) for inbound routing
        self._mqtt_topic_map = {}

        self._setup_mqtt()
        self._setup_ros2_to_mqtt()
        self._setup_mqtt_to_ros2()
        self.mqtt_client.loop_start()
        self.create_timer(0.01, self._drain_m2r_queue)

    def _setup_mqtt(self):
        broker = self.get_parameter('mqtt_broker').get_parameter_value().string_value
        port = self.get_parameter('mqtt_port').get_parameter_value().integer_value

        self.mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        self.mqtt_client.on_connect = self._on_mqtt_connect
        self.mqtt_client.on_message = self._on_mqtt_message
        self.mqtt_client.connect(broker, port)
        self.get_logger().info(f'Connecting to MQTT broker: {broker}:{port}')

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
        _STR_TYPE = 'std_msgs/msg/String'
        for mapping in self.config.get('ros2_to_mqtt', []):
            ros_topic  = mapping['ros_topic']
            mqtt_topic = mapping['mqtt_topic']
            ros_type   = mapping.get('msg_type', _STR_TYPE)
            msg_type   = load_msg_type(ros_type)
            fmt        = mapping.get('format', 'cdr')
            qos        = _qos_from_mapping(mapping)
            serialize  = (lambda msg, rt=ros_type: msg_to_json(msg, rt)) if fmt == 'json' else msg_to_bytes
            cb = lambda msg, t=mqtt_topic, s=serialize: (
                self.mqtt_client.publish(t, s(msg)),
                self.get_logger().debug(f'R2M: {t}')
            )
            self.ros_subs.append(self.create_subscription(msg_type, ros_topic, cb, qos))

    def _setup_mqtt_to_ros2(self):
        _STR_TYPE = 'std_msgs/msg/String'
        for mapping in self.config.get('mqtt_to_ros2', []):
            mqtt_topic  = mapping['mqtt_topic']
            ros_topic   = mapping['ros_topic']
            ros_type    = mapping.get('msg_type', _STR_TYPE)
            fmt         = mapping.get('format', 'cdr')
            wire_type   = _STR_TYPE if fmt == 'json' else ros_type
            pub_type    = load_msg_type(wire_type)
            m_type      = load_msg_type(ros_type)
            qos         = _qos_from_mapping(mapping)
            pub         = self.create_publisher(pub_type, ros_topic, qos)
            deserialize = (lambda data, mt=m_type: json_to_msg(data, mt)) if fmt == 'json' \
                     else (lambda data, mt=m_type: bytes_to_msg(data, mt))
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
