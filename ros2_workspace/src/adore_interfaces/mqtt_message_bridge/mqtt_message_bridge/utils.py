import importlib
import json
import os
import re
import datetime
from rclpy.serialization import serialize_message, deserialize_message
from rosidl_runtime_py import message_to_ordereddict, set_message_fields


def ensure_self_signed_cert(
    store_dir: str | None = None,
    common_name: str = 'mqtt_bridge',
    validity_days: int = 3650,
) -> tuple[str, str]:
    """Return (certfile, keyfile) paths, generating them if they don't exist.

    Files are written to store_dir (default: ~/.ros/mqtt_bridge/) and are
    only created once -- subsequent calls are a no-op as long as the files exist.
    """
    from cryptography import x509
    from cryptography.x509.oid import NameOID
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa

    if store_dir is None:
        store_dir = os.path.join(os.path.expanduser('~'), '.ros', 'mqtt_bridge')

    os.makedirs(store_dir, mode=0o700, exist_ok=True)

    key_path  = os.path.join(store_dir, 'client.key')
    cert_path = os.path.join(store_dir, 'client.crt')

    if os.path.exists(key_path) and os.path.exists(cert_path):
        return cert_path, key_path

    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

    with open(key_path, 'wb') as f:
        f.write(key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        ))
    os.chmod(key_path, 0o600)

    subject = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, common_name)])
    now = datetime.datetime.now(datetime.timezone.utc)
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(subject)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now)
        .not_valid_after(now + datetime.timedelta(days=validity_days))
        .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
        .sign(key, hashes.SHA256())
    )

    with open(cert_path, 'wb') as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))

    return cert_path, key_path



def load_msg_type(msg_type_str: str):
    try:
        pkg, interface, name = msg_type_str.split('/')
    except ValueError:
        raise ValueError(f"Invalid msg_type '{msg_type_str}'. Expected 'pkg/msg/Name'.")
    module = importlib.import_module(f'{pkg}.{interface}')
    return getattr(module, name)


def msg_to_bytes(msg) -> bytes:
    return serialize_message(msg)


def bytes_to_msg(data: bytes, msg_type):
    return deserialize_message(data, msg_type)


def msg_to_json(msg, ros_type: str) -> bytes:
    """Serialize to raw JSON bytes with datatype metadata. Bridge-to-bridge only."""
    obj = message_to_ordereddict(msg)
    obj['datatype'] = ros_type
    return json.dumps(obj).encode('utf-8')


def json_to_msg(data: bytes, msg_type):
    """Deserialize raw JSON bytes to a ROS message, stripping metadata fields."""
    obj = json.loads(data.decode('utf-8'))
    obj.pop('datatype', None)
    obj.pop('topic', None)
    msg = msg_type()
    set_message_fields(msg, obj)
    return msg


def msg_to_cdr_json(msg, ros_type: str) -> bytes:
    """Serialize to CDR-encoded std_msgs/msg/String whose data field is JSON with datatype metadata.
    Consumable by native rmw_zenoh_cpp subscribers via ros2 topic echo."""
    from std_msgs.msg import String
    obj = message_to_ordereddict(msg)
    obj['datatype'] = ros_type
    wrapper = String()
    wrapper.data = json.dumps(obj)
    return serialize_message(wrapper)


def cdr_json_to_msg(data: bytes, msg_type):
    """Deserialize a CDR std_msgs/msg/String containing JSON back into msg_type."""
    from std_msgs.msg import String
    wrapper = deserialize_message(data, String)
    obj = json.loads(wrapper.data)
    obj.pop('datatype', None)
    obj.pop('topic', None)
    msg = msg_type()
    set_message_fields(msg, obj)
    return msg


def raw_to_str_msg(data: bytes):
    """Wrap an opaque MQTT payload verbatim in std_msgs/msg/String."""
    from std_msgs.msg import String
    msg = String()
    msg.data = data.decode('utf-8', errors='replace')
    return msg


def str_msg_to_raw(msg) -> bytes:
    return msg.data.encode('utf-8')


_TOPIC_PLACEHOLDER = re.compile(r'\{(\w+)\}')


def mqtt_topic_resolver(mqtt_topic: str):
    """None without placeholders, otherwise a function filling each {field}
    from the top-level field of the same name in a JSON object."""
    if not _TOPIC_PLACEHOLDER.search(mqtt_topic):
        return None

    def resolve(payload: bytes) -> str:
        obj = json.loads(payload)
        if not isinstance(obj, dict):
            raise ValueError('payload is not a JSON object')

        def level(match):
            field = match.group(1)
            value = obj.get(field)
            if isinstance(value, bool) or not isinstance(value, (str, int)):
                raise ValueError(f"field '{field}' is missing or not a string")
            value = str(value)
            if not value or any(c in value for c in '/+#\0'):
                raise ValueError(f"field '{field}' is not a valid topic level: '{value}'")
            return value

        return _TOPIC_PLACEHOLDER.sub(level, mqtt_topic)

    return resolve


def mqtt_topic_filter(mqtt_topic: str) -> str:
    """Subscription filter for a topic with placeholders: each {field} becomes '+'."""
    return _TOPIC_PLACEHOLDER.sub('+', mqtt_topic)


def mqtt_topic_fields(mqtt_topic: str):
    """None without placeholders, otherwise a function returning {field: level}
    for a topic matched by mqtt_topic_filter(mqtt_topic)."""
    fields = {}
    for index, level in enumerate(mqtt_topic.split('/')):
        match = _TOPIC_PLACEHOLDER.fullmatch(level)
        if match:
            fields[index] = match.group(1)
        elif _TOPIC_PLACEHOLDER.search(level):
            raise ValueError(f"placeholder in '{level}' of {mqtt_topic} must fill the whole topic level")
    if not fields:
        return None

    def extract(topic: str) -> dict:
        levels = topic.split('/')
        return {field: levels[index] for index, field in fields.items()}

    return extract


def add_topic_fields(payload: bytes, fields: dict) -> tuple[bytes, list]:
    """Add the fields a JSON object lacks. Differing values are returned."""
    obj = json.loads(payload)
    if not isinstance(obj, dict):
        raise ValueError('payload is not a JSON object')
    conflicts = [field for field, value in fields.items() if field in obj and obj[field] != value]
    missing = {field: value for field, value in fields.items() if field not in obj}
    if not missing:
        return payload, conflicts
    obj.update(missing)
    return json.dumps(obj, ensure_ascii=False).encode('utf-8'), conflicts
