# ********************************************************************************
# Copyright (c) 2026 Contributors to the Eclipse Foundation
#
# See the NOTICE file(s) distributed with this work for additional
# information regarding copyright ownership.
#
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# https://www.eclipse.org/legal/epl-2.0
#
# SPDX-License-Identifier: EPL-2.0
# ********************************************************************************

import importlib
import json
from rosidl_runtime_py.convert import message_to_ordereddict
from rosidl_runtime_py import set_message_fields

def load_msg_type(msg_type_str: str):
    try:
        pkg, interface, name = msg_type_str.split('/')
    except ValueError:
        raise ValueError(f"Invalid msg_type '{msg_type_str}'. Expected 'pkg/msg/Name'.")
    module = importlib.import_module(f'{pkg}.{interface}')
    return getattr(module, name)

def msg_to_bytes(msg) -> bytes:
    return json.dumps(dict(message_to_ordereddict(msg))).encode('utf-8')

def bytes_to_msg(data: bytes, msg_type):
    msg = msg_type()
    set_message_fields(msg, json.loads(data.decode('utf-8')))
    return msg
