"""
Codec: translates between proto messages and ROS messages.

All logic for packing/unpacking proto oneofs lives here so bridge_node.py
stays free of serialization concerns.
"""

import json
import sys
from typing import Any, Callable, Optional

from rclpy.serialization import serialize_message, deserialize_message
from rosidl_runtime_py import message_to_ordereddict, set_message_fields

_STR_TYPE = 'std_msgs/msg/String'


# ---------------------------------------------------------------------------
# ROS type loading
# ---------------------------------------------------------------------------

def load_ros_type(msg_type_str: str):
    pkg, interface, name = msg_type_str.split('/')
    import importlib
    return getattr(importlib.import_module(f'{pkg}.{interface}'), name)


def wire_ros_type(ros_type: str, fmt: str) -> str:
    """The actual ROS type that travels on the wire (may differ from logical type for json formats)."""
    return _STR_TYPE if fmt in ('json', 'cdr_json') else ros_type


# ---------------------------------------------------------------------------
# ROS serializers / deserializers
# ---------------------------------------------------------------------------

def make_ros_serializer(ros_type: str, fmt: str) -> Callable:
    if fmt == 'json':
        def _to_json(msg, rt=ros_type) -> bytes:
            obj = message_to_ordereddict(msg)
            obj['datatype'] = rt
            return json.dumps(obj).encode()
        return _to_json

    if fmt == 'cdr_json':
        def _to_cdr_json(msg, rt=ros_type) -> bytes:
            from std_msgs.msg import String
            obj = message_to_ordereddict(msg)
            obj['datatype'] = rt
            wrapper = String(data=json.dumps(obj))
            return serialize_message(wrapper)
        return _to_cdr_json

    return serialize_message


def make_ros_deserializer(msg_type, fmt: str) -> Callable:
    if fmt == 'json':
        def _from_json(data: bytes, mt=msg_type):
            obj = json.loads(data.decode())
            obj.pop('datatype', None)
            obj.pop('topic', None)
            msg = mt()
            set_message_fields(msg, obj)
            return msg
        return _from_json

    if fmt == 'cdr_json':
        def _from_cdr_json(data: bytes, mt=msg_type):
            from std_msgs.msg import String
            wrapper = deserialize_message(data, String)
            obj = json.loads(wrapper.data)
            obj.pop('datatype', None)
            obj.pop('topic', None)
            msg = mt()
            set_message_fields(msg, obj)
            return msg
        return _from_cdr_json

    return lambda data, mt=msg_type: deserialize_message(data, mt)


# ---------------------------------------------------------------------------
# Proto <-> bytes
# ---------------------------------------------------------------------------

def proto_field_to_bytes(proto_msg: Any, field_name: str, fmt: str) -> Optional[bytes]:
    """
    Extract a field from a proto message and return it as bytes suitable
    for feeding to a ROS deserializer.

    For json/cdr_json formats the field value is serialized to JSON bytes.
    For cdr the field value is serialized to proto bytes (caller's ROS
    deserializer must accept them).
    """
    field_desc = type(proto_msg).DESCRIPTOR.fields_by_name.get(field_name)
    if field_desc is None:
        return None

    value = getattr(proto_msg, field_name, None)
    if value is None:
        return None

    # Scalar bytes/string -- return directly.
    if field_desc.type in (field_desc.TYPE_BYTES, field_desc.TYPE_STRING):
        return value if isinstance(value, bytes) else value.encode()

    if fmt in ('json', 'cdr_json'):
        # Serialize proto message to dict then to JSON bytes.
        d = _proto_to_dict(value)
        return json.dumps(d).encode()

    # cdr: serialize proto message to its binary wire format.
    return value.SerializeToString()


def proto_field_set(proto_msg_cls, field_name: str, payload: bytes, fmt: str) -> Any:
    """
    Create a new proto message of proto_msg_cls with field_name set from payload bytes.
    payload is what came out of a ROS serializer.
    """
    instance   = proto_msg_cls()
    field_desc = proto_msg_cls.DESCRIPTOR.fields_by_name.get(field_name)
    if field_desc is None:
        raise ValueError(f'Field {field_name!r} not found on {proto_msg_cls.DESCRIPTOR.name}')

    # Scalar bytes/string -- set directly.
    if field_desc.type in (field_desc.TYPE_BYTES, field_desc.TYPE_STRING):
        setattr(instance, field_name, payload)
        return instance

    # Nested message -- find its class and populate.
    nested_cls = _find_proto_class(field_desc.message_type.full_name)
    if nested_cls is None:
        raise LookupError(f'Cannot resolve proto class: {field_desc.message_type.full_name}')

    if fmt in ('json', 'cdr_json'):
        d = json.loads(payload.decode())
        _dict_to_proto(nested_cls, d, getattr(instance, field_name))
    else:
        getattr(instance, field_name).MergeFrom(nested_cls.FromString(payload))

    return instance


# ---------------------------------------------------------------------------
# oneof dispatch
# ---------------------------------------------------------------------------

def active_oneof_field(proto_msg: Any) -> str:
    """Return the name of the set oneof branch, or '' if none."""
    for oneof in type(proto_msg).DESCRIPTOR.oneofs:
        f = proto_msg.WhichOneof(oneof.name)
        if f:
            return f
    return ''


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _proto_to_dict(msg) -> dict:
    """Shallow proto-message-to-dict, suitable for JSON serialization."""
    from google.protobuf.json_format import MessageToDict
    return MessageToDict(msg, preserving_proto_field_name=True, including_default_value_fields=False)


def _dict_to_proto(proto_cls, d: dict, target=None):
    from google.protobuf.json_format import ParseDict
    return ParseDict(d, target if target is not None else proto_cls())


def _find_proto_class(full_name: str) -> Optional[type]:
    from google.protobuf import symbol_database
    try:
        return symbol_database.Default().GetSymbol(full_name)
    except KeyError:
        pass
    # Fall back to scanning loaded _pb2 modules.
    for mod in list(sys.modules.values()):
        if not getattr(mod, '__name__', '').endswith('_pb2'):
            continue
        for attr in dir(mod):
            obj = getattr(mod, attr, None)
            try:
                if obj and hasattr(obj, 'DESCRIPTOR') and obj.DESCRIPTOR.full_name == full_name:
                    return obj
            except Exception:
                pass
    return None
