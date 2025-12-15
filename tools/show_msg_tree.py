#!/usr/bin/env python3
# ********************************************************************************
# Copyright (c) 2025 Contributors to the Eclipse Foundation
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


# -*- coding: utf-8 -*-
"""
Recursively pretty-print a ROS 2 message definition as a tree.

usage:
    ./show_msg_tree.py <package/msg/Type>
example:
    ./show_msg_tree.py adore_ros2_msgs/msg/TrafficParticipant
"""
from __future__ import annotations

import re
import sys
from functools import lru_cache
from typing import Dict, List, Optional, Set, Tuple

from rosidl_runtime_py.utilities import get_message

# ------------------------- IDL parsing helpers -------------------------

# Include common aliases you’ll see from get_fields_and_field_types()
PRIMITIVES = {
    # canonical IDL
    "bool", "byte", "char", "float", "double", "long double",
    "int8", "uint8", "int16", "uint16", "int32", "uint32", "int64", "uint64",
    "string", "wstring",
    # frequent variants emitted by generators
    "boolean", "float32", "float64",
}

RE_BOUNDED_STRING = re.compile(
    r"^(w?string)(?:<=\d+)?$")                 # string<=N
RE_SEQUENCE = re.compile(
    r"^sequence<\s*(.+?)\s*(?:,\s*\d+\s*)?>$")       # sequence<T[,N]>
# T[] or T[N]
RE_ARRAY = re.compile(r"^(.+?)\s*\[\s*(\d*)\s*\]$")

# Accept either "pkg/msg/Type" or "pkg/Type"
RE_MSG = re.compile(r"^[A-Za-z]\w*/(?:msg/)?[A-Za-z]\w*$")


def is_primitive(token: str) -> bool:
    return token in PRIMITIVES or bool(RE_BOUNDED_STRING.match(token))


def is_msg_type(token: str) -> bool:
    return bool(RE_MSG.match(token))


def normalize_slot(slot: str) -> Tuple[str, Optional[str], Optional[str]]:
    """
    Normalize a field type string into (kind, elem, meta).
    kind ∈ {"primitive", "array", "sequence", "message", "other"}
      - primitive: elem=slot
      - array:     elem=element type, meta="" or size ("" means unbounded '[]')
      - sequence:  elem=element type
      - message:   elem=fully qualified type (pkg/(msg/)?Type)
    """
    s = slot.strip()

    m = RE_ARRAY.match(s)
    if m:
        elem = m.group(1).strip()
        size = m.group(2) or ""
        return "array", elem, size

    m = RE_SEQUENCE.match(s)
    if m:
        elem = m.group(1).strip()
        return "sequence", elem, None

    if is_primitive(s):
        return "primitive", s, None

    if is_msg_type(s):
        return "message", s, None

    return "other", s, None

# ------------------------- Introspection + printing -------------------------


@lru_cache(maxsize=512)
def resolve_msg_cls(type_name: str):
    return get_message(type_name)


@lru_cache(maxsize=512)
def fields_of(type_name: str) -> Dict[str, str]:
    cls = resolve_msg_cls(type_name)
    inst = cls()
    return inst.get_fields_and_field_types()


def _branch_prefixes(n: int) -> List[Tuple[str, bool]]:
    return [("└── " if i == n - 1 else "├── ", i == n - 1) for i in range(n)]


def _indent_for(parents_last: List[bool]) -> str:
    return "".join("    " if is_last else "│   " for is_last in parents_last)


def _container_suffix(kind: str, meta: Optional[str]) -> str:
    if kind == "array":
        return "[]" if meta == "" else f"[{meta}]"
    if kind == "sequence":
        return "[]"
    return ""


def _print_subtree(
    subtype: str,
    parents_last: List[bool],
    seen_path: Set[str],
    max_depth: int,
) -> None:
    indent = _indent_for(parents_last)

    if subtype in seen_path:
        print(f"{indent}↳ (already expanded)")
        return
    if len(parents_last) >= max_depth:
        print(f"{indent}… (max depth reached)")
        return

    try:
        items = list(fields_of(subtype).items())
    except Exception as exc:
        print(f"{indent}<introspection failed: {exc}>")
        return

    seen_path.add(subtype)

    branches = _branch_prefixes(len(items))
    for (field_name, slot), (connector, is_last) in zip(items, branches):
        prefix = _indent_for(parents_last) + connector
        kind, elem, meta = normalize_slot(slot)
        cont = _container_suffix(kind, meta)

        if kind == "primitive":
            print(f"{prefix}{field_name}: {cont}{elem}")
            continue

        if kind in ("array", "sequence"):
            # container of something
            if is_primitive(elem):
                print(f"{prefix}{field_name}: {cont}{elem}")
            elif is_msg_type(elem):
                print(f"{prefix}{field_name}: {cont}{elem}")
                _print_subtree(elem, parents_last +
                               [is_last], seen_path, max_depth)
            else:
                print(f"{prefix}{field_name}: {cont}{elem}")
            continue

        if kind == "message":
            print(f"{prefix}{field_name}: {elem}")
            _print_subtree(elem, parents_last +
                           [is_last], seen_path, max_depth)
            continue

        # fallback
        print(f"{prefix}{field_name}: {slot}")

    seen_path.remove(subtype)


def main() -> None:
    if len(sys.argv) != 2:
        print("usage: show_msg_tree.py <package/msg/Type>")
        sys.exit(1)

    type_name = sys.argv[1].strip()
    print(type_name)
    _print_subtree(type_name, [], set(), max_depth=64)


if __name__ == "__main__":
    main()
