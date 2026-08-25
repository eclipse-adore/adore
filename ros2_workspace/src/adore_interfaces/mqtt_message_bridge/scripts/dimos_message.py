#!/usr/bin/env python3
"""Build and structurally validate solbox notification messages.

    python3 scripts/dimos_message.py --generate [--action-id N]
    python3 scripts/dimos_message.py --validate FILE

Validation checks only that the fields the bridge and its consumers rely on are
present and hold the expected JSON types. Values are not constrained: the
publisher owns them, and the observed traffic uses cause codes, station types
and intervals beyond any fixed list.
"""
import argparse
import json
import random
import sys
from datetime import datetime, timezone

TIME_FORMAT = '%Y-%m-%d %H:%M:%S'

NUMBER = (int, float)

REQUIRED_FIELDS = (
    ('header.protocol_ver', str),
    ('header.msg_type', str),
    ('header.origin_station_id', (str, int)),
    ('payload.management.action_id', (str, int)),
    ('payload.management.detection_time', str),
    ('payload.management.reference_time', str),
    ('payload.management.termination', int),
    ('payload.management.event_position.lat', NUMBER),
    ('payload.management.event_position.lon', NUMBER),
    ('payload.management.event_position.alt', NUMBER),
    ('payload.management.awareness_distance', NUMBER),
    ('payload.management.transmission_interval', NUMBER),
    ('payload.management.station_type', int),
    ('payload.situation.event_type.cause_code', str),
    ('payload.situation.road_type', int),
    ('alacarte', dict),
)


def build(msg_type: str = 'warning', station_id: str = 'solbox_test', action_id: int | None = None) -> dict:
    now = datetime.now(timezone.utc).strftime(TIME_FORMAT)
    action_id = random.randrange(10**8, 10**9) if action_id is None else action_id
    message = {
        'header': {
            'protocol_ver': '0.1.0',
            'msg_type': msg_type,
            'origin_station_id': station_id,
        },
        'payload': {
            'management': {
                'action_id': action_id,
                'detection_time': now,
                'reference_time': now,
                'termination': 0,
                'event_position': {'lat': 47.0, 'lon': 12.0, 'alt': 550},
                'awareness_distance': 500.0,
                'transmission_interval': 4,
                'station_type': 15,
            },
            'situation': {
                'event_type': {'cause_code': 'pos'},
                'road_type': 10,
            },
        },
        'alacarte': {
            'warning': {'continuity': {'r_hpl': 100.0}},
        },
    }
    if msg_type == 'alert':
        message['alacarte']['alert'] = {
            'accuracy': {'hpe': 10.0},
            'integrity': {'hpl': 100.0},
        }
    return message


def _get(obj, path):
    for key in path.split('.'):
        if not isinstance(obj, dict) or key not in obj:
            return None
        obj = obj[key]
    return obj


def _type_names(types) -> str:
    if isinstance(types, type):
        return types.__name__
    return ' or '.join(t.__name__ for t in types)


def validate(message) -> list:
    if not isinstance(message, dict):
        return ['message is not a JSON object']

    errors = []
    for path, types in REQUIRED_FIELDS:
        value = _get(message, path)
        if value is None:
            errors.append(f'missing field: {path}')
        elif isinstance(value, bool) or not isinstance(value, types):
            errors.append(f'{path} has type {type(value).__name__}, expected {_type_names(types)}')

    for path in ('payload.management.detection_time', 'payload.management.reference_time'):
        value = _get(message, path)
        if isinstance(value, str):
            try:
                datetime.strptime(value, TIME_FORMAT)
            except ValueError:
                errors.append(f'{path} is {value!r}, expected format yyyy-MM-dd hh:mm:ss')

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--generate', action='store_true')
    group.add_argument('--validate', metavar='FILE', help='file to read, or - for stdin')
    parser.add_argument('--msg-type', default='warning')
    parser.add_argument('--station-id', default='solbox_test')
    parser.add_argument('--action-id', type=int, default=None)
    args = parser.parse_args()

    if args.generate:
        print(json.dumps(build(args.msg_type, args.station_id, args.action_id)))
        return 0

    raw = sys.stdin.read() if args.validate == '-' else open(args.validate).read()
    try:
        message = json.loads(raw)
    except ValueError as exc:
        print(f'not valid JSON: {exc}')
        return 1

    errors = validate(message)
    for error in errors:
        print(f'error: {error}')
    if not errors:
        cause = _get(message, 'payload.situation.event_type.cause_code')
        msg_type = _get(message, 'header.msg_type')
        print(f'structure valid (msg_type={msg_type!r}, cause_code={cause!r})')
    return 1 if errors else 0


if __name__ == '__main__':
    sys.exit(main())
