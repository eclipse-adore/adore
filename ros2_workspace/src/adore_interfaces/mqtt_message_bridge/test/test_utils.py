import json
import os
import tempfile
import unittest

try:
    from std_msgs.msg import String
except ImportError as exc:
    raise unittest.SkipTest(f'ROS 2 environment not sourced: {exc}')

from mqtt_message_bridge.utils import (
    bytes_to_msg,
    cdr_json_to_msg,
    ensure_self_signed_cert,
    json_to_msg,
    load_msg_type,
    msg_to_bytes,
    msg_to_cdr_json,
    msg_to_json,
    raw_to_str_msg,
    str_msg_to_raw,
)

STR_TYPE = 'std_msgs/msg/String'


class LoadMsgTypeTestCase(unittest.TestCase):
    def test_resolves_a_valid_type(self):
        self.assertIs(load_msg_type(STR_TYPE), String)

    def test_rejects_a_malformed_type(self):
        with self.assertRaises(ValueError):
            load_msg_type('std_msgs/String')


class SerializationTestCase(unittest.TestCase):
    def setUp(self):
        self.msg = String(data='hello bridge')

    def test_cdr_round_trip(self):
        self.assertEqual(bytes_to_msg(msg_to_bytes(self.msg), String).data, self.msg.data)

    def test_json_round_trip_strips_metadata(self):
        payload = msg_to_json(self.msg, STR_TYPE)
        self.assertEqual(json.loads(payload.decode())['datatype'], STR_TYPE)
        self.assertEqual(json_to_msg(payload, String).data, self.msg.data)

    def test_cdr_json_is_readable_as_a_plain_string_message(self):
        payload = msg_to_cdr_json(self.msg, STR_TYPE)
        wrapper = bytes_to_msg(payload, String)
        self.assertEqual(json.loads(wrapper.data)['data'], self.msg.data)
        self.assertEqual(cdr_json_to_msg(payload, String).data, self.msg.data)

    def test_raw_round_trip_is_byte_exact(self):
        self.assertEqual(str_msg_to_raw(self.msg), b'hello bridge')
        self.assertEqual(raw_to_str_msg(b'hello bridge').data, self.msg.data)

    def test_raw_decode_tolerates_invalid_utf8(self):
        self.assertIsInstance(raw_to_str_msg(b'\xff\xfe').data, str)


class CertGenerationTestCase(unittest.TestCase):
    def test_generates_once_and_reuses(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = os.path.join(tmp, 'store')
            cert, key = ensure_self_signed_cert(store, 'test_cn', 1)
            self.assertTrue(os.path.exists(cert) and os.path.exists(key))
            self.assertEqual(os.stat(key).st_mode & 0o777, 0o600)
            mtime = os.stat(cert).st_mtime_ns
            self.assertEqual(ensure_self_signed_cert(store, 'test_cn', 1), (cert, key))
            self.assertEqual(os.stat(cert).st_mtime_ns, mtime)


if __name__ == '__main__':
    unittest.main()
