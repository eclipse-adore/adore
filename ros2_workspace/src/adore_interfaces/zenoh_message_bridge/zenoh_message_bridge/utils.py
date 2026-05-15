import importlib
from rclpy.serialization import serialize_message, deserialize_message


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
