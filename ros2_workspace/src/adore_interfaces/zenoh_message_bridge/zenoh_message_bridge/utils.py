import importlib
import json
from rclpy.serialization import serialize_message, deserialize_message
from rosidl_runtime_py import message_to_ordereddict, set_message_fields


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
