import copy
import json
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'scripts'))

from dimos_message import build, validate

# Observed on od_imoger/solbox/+/notifications.
LIVE_SAMPLES = [
    json.loads('''
    {
        "header": {"protocol_ver": "0.1.0", "msg_type": "warning", "origin_station_id": "solbox1"},
        "payload": {
            "management": {
                "action_id": 73501,
                "detection_time": "2026-08-10 09:30:45",
                "reference_time": "2026-08-10 09:30:45",
                "termination": 1,
                "event_position": {"lat": 46.852173, "lon": 12.460039, "alt": 637.3},
                "awareness_distance": 139.5,
                "transmission_interval": 2,
                "station_type": 10
            },
            "situation": {"event_type": {"cause_code": "pos"}, "road_type": 2}
        },
        "alacarte": {
            "warning": {"continuity": {"r_hpl": 146.6}},
            "alert": {"accuracy": {"hpe": 11.5}, "integrity": {"hpl": 98.6}}
        }
    }
    '''),
    json.loads('''
    {
        "header": {"protocol_ver": "0.1.0", "msg_type": "warning", "origin_station_id": "solbox1"},
        "payload": {
            "management": {
                "action_id": 91422,
                "detection_time": "2026-08-10 09:41:02",
                "reference_time": "2026-08-10 09:41:02",
                "termination": 0,
                "event_position": {"lat": 46.85, "lon": 12.46, "alt": 640.1},
                "awareness_distance": 172.9,
                "transmission_interval": 10,
                "station_type": 10
            },
            "situation": {"event_type": {"cause_code": "integrity"}, "road_type": 5}
        },
        "alacarte": {"warning": {"continuity": {"r_hpl": 150.0}}}
    }
    '''),
]


class ValidatorTestCase(unittest.TestCase):
    def test_live_samples_are_accepted(self):
        for index, sample in enumerate(LIVE_SAMPLES):
            self.assertEqual(validate(sample), [], f'sample {index}')

    def test_values_are_not_constrained(self):
        message = copy.deepcopy(LIVE_SAMPLES[0])
        message['payload']['situation']['event_type']['cause_code'] = 'anything'
        message['payload']['situation']['road_type'] = 99
        message['payload']['management']['station_type'] = 3
        message['payload']['management']['transmission_interval'] = 17
        message['payload']['management']['awareness_distance'] = 12.5
        message['header']['msg_type'] = 'something_new'
        self.assertEqual(validate(message), [])

    def test_generated_messages_are_accepted(self):
        for msg_type in ('warning', 'alert'):
            self.assertEqual(validate(build(msg_type)), [], msg_type)

    def test_generated_action_id_is_used_verbatim(self):
        self.assertEqual(build(action_id=4242)['payload']['management']['action_id'], 4242)

    def test_missing_field_is_an_error(self):
        broken = copy.deepcopy(LIVE_SAMPLES[0])
        del broken['payload']['management']['action_id']
        self.assertTrue(any('action_id' in e for e in validate(broken)))

    def test_wrong_type_is_an_error(self):
        broken = copy.deepcopy(LIVE_SAMPLES[0])
        broken['payload']['management']['event_position']['lat'] = 'north'
        self.assertTrue(any('lat' in e for e in validate(broken)))

    def test_booleans_are_not_accepted_as_numbers(self):
        broken = copy.deepcopy(LIVE_SAMPLES[0])
        broken['payload']['management']['termination'] = True
        self.assertTrue(any('termination' in e for e in validate(broken)))

    def test_timestamp_format_is_checked(self):
        broken = copy.deepcopy(LIVE_SAMPLES[0])
        broken['payload']['management']['detection_time'] = '2025-07-23T13:00:00Z'
        self.assertTrue(any('detection_time' in e for e in validate(broken)))

    def test_non_object_payload_is_rejected(self):
        self.assertEqual(len(validate([1, 2, 3])), 1)


if __name__ == '__main__':
    unittest.main()
