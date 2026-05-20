import json
import re
import socket
import threading

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, DurabilityPolicy, ReliabilityPolicy
from std_msgs.msg import String

from .hardware_utils import (
    get_system_info,
    get_cpu_info,
    get_ram_info,
    get_accelerator_info,
    get_pci_devices,
    get_usb_devices,
    get_serial_devices,
    get_network_interfaces,
    get_storage_devices,
    get_sensor_devices,
    get_audio_devices,
    get_input_devices,
    get_power_info,
)

INVENTORY_TOPIC = '/cluster/hardware_inventory'


class HardwareDiscoveryNode(Node):
    def __init__(self, context=None):
        super().__init__('hardware_discovery_node', context=context)

        self.declare_parameter('publish_rate_hz', 0.1)
        self.declare_parameter('node_name', '')

        rate = self.get_parameter('publish_rate_hz').get_parameter_value().double_value
        param_name = self.get_parameter('node_name').get_parameter_value().string_value.strip()
        self._node_name = param_name if param_name else socket.gethostname()
        # ROS 2 topic names only allow [a-zA-Z0-9_~{}] - sanitize for topic use
        self._topic_host = re.sub(r'[^a-zA-Z0-9_]', '_', self._node_name)
        self.get_logger().info(f'hardware_id resolved to: {self._node_name} (topic key: {self._topic_host})')

        # Per-host topic: /cluster/<hostname>/hardware_inventory
        inventory_topic = f'/cluster/{self._topic_host}/hardware_inventory'

        latched_qos = QoSProfile(
            depth=1,
            durability=DurabilityPolicy.TRANSIENT_LOCAL,
            reliability=ReliabilityPolicy.RELIABLE,
        )
        self._pub = self.create_publisher(String, inventory_topic, latched_qos)

        self._payload: str | None = None
        self._lock = threading.Lock()

        threading.Thread(target=self._probe_hardware, daemon=True).start()

        self._timer = self.create_timer(1.0 / rate, self._publish_inventory)
        self.get_logger().info(f'HardwareDiscoveryNode started on {self._node_name} @ {rate} Hz → {inventory_topic}')

    def _probe_hardware(self):
        self.get_logger().info('Probing hardware inventory...')
        try:
            payload = self._build_inventory()
            with self._lock:
                self._payload = json.dumps(payload, indent=2, default=str)
            self.get_logger().info('Hardware inventory ready')
        except Exception as e:
            self.get_logger().error(f'Hardware probe failed: {e}')

    def _build_inventory(self) -> dict:
        return {
            'hostname': self._node_name,
            'system': get_system_info(),
            'cpu': get_cpu_info(),
            'ram': get_ram_info(),
            'accelerators': get_accelerator_info(),
            'pci': get_pci_devices(),
            'usb': get_usb_devices(),
            'serial': get_serial_devices(),
            'network': get_network_interfaces(),
            'storage': get_storage_devices(),
            'sensors': get_sensor_devices(),
            'audio': get_audio_devices(),
            'input': get_input_devices(),
            'power': get_power_info(),
        }

    def _publish_inventory(self):
        with self._lock:
            payload = self._payload

        if payload is None:
            self.get_logger().debug('Inventory not ready yet; skipping publish')
            return

        self._pub.publish(String(data=payload))
        self.get_logger().debug('Published hardware inventory')


def main(args=None):
    rclpy.init(args=args)
    node = HardwareDiscoveryNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()
