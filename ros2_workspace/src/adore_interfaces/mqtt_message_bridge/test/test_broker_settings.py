import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'scripts'))

from bridge_mqtt_args import broker_args
from mqtt_broker import as_bool, load_settings, port_speaks_tls, reason_text

BASE_CONFIG = """
mqtt:
  host: config-host
  port: 1884
  keepalive: 30
  auth:
    username_env: MQTT_USERNAME
    password_env: MQTT_PASSWORD
  tls:
    enabled: false
"""

TLS_CONFIG = """
mqtt:
  host: secure-host
  port: 8883
  env_file: {env_file}
  auth:
    username_env: MQTT_USERNAME
    password_env: MQTT_PASSWORD
  tls:
    enabled: true
    ca_certs: broker.crt
    certfile: client.crt
    keyfile: client.key
    insecure: true
"""


class SettingsTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.saved_env = {k: os.environ.get(k) for k in (
            'MQTT_HOST', 'MQTT_PORT', 'MQTT_TLS', 'MQTT_USERNAME', 'MQTT_PASSWORD',
            'MQTT_BRIDGE_CERT_DIR', 'MQTT_BRIDGE_CONFIG', 'MQTT_KEEPALIVE',
        )}
        for key in self.saved_env:
            os.environ.pop(key, None)
        self.addCleanup(self._restore_env)

    def _restore_env(self):
        for key, value in self.saved_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

    def write(self, name, text):
        path = os.path.join(self.tmp.name, name)
        with open(path, 'w') as f:
            f.write(text)
        return path

    def test_values_come_from_config_when_env_is_unset(self):
        settings = load_settings(self.write('a.yaml', BASE_CONFIG))
        self.assertEqual(settings.host, 'config-host')
        self.assertEqual(settings.port, 1884)
        self.assertEqual(settings.keepalive, 30)
        self.assertFalse(settings.tls)

    def test_environment_overrides_config(self):
        os.environ['MQTT_HOST'] = 'env-host'
        os.environ['MQTT_PORT'] = '9999'
        settings = load_settings(self.write('b.yaml', BASE_CONFIG))
        self.assertEqual(settings.address, 'env-host:9999')

    def test_env_file_does_not_override_real_environment(self):
        env_file = self.write('secrets.env', 'MQTT_HOST=file-host\nMQTT_USERNAME=file-user\n')
        os.environ['MQTT_HOST'] = 'env-host'
        settings = load_settings(self.write('c.yaml', TLS_CONFIG.format(env_file=env_file)))
        self.assertEqual(settings.host, 'env-host')
        self.assertEqual(settings.username, 'file-user')

    def test_relative_tls_paths_resolve_against_cert_dir(self):
        cert_dir = os.path.join(self.tmp.name, 'certs')
        os.makedirs(cert_dir)
        for name in ('broker.crt', 'client.crt', 'client.key'):
            open(os.path.join(cert_dir, name), 'w').close()
        os.environ['MQTT_BRIDGE_CERT_DIR'] = cert_dir
        env_file = self.write('empty.env', '')
        settings = load_settings(self.write('d.yaml', TLS_CONFIG.format(env_file=env_file)))
        self.assertTrue(settings.tls)
        self.assertEqual(settings.ca_certs, os.path.join(cert_dir, 'broker.crt'))
        self.assertEqual(settings.missing, [])

    def test_missing_tls_material_is_reported(self):
        os.environ['MQTT_BRIDGE_CERT_DIR'] = os.path.join(self.tmp.name, 'nope')
        env_file = self.write('empty2.env', '')
        settings = load_settings(self.write('e.yaml', TLS_CONFIG.format(env_file=env_file)))
        self.assertEqual(len(settings.missing), 3)

    def test_mosquitto_args_carry_credentials_and_tls(self):
        cert_dir = os.path.join(self.tmp.name, 'certs2')
        os.makedirs(cert_dir)
        for name in ('broker.crt', 'client.crt', 'client.key'):
            open(os.path.join(cert_dir, name), 'w').close()
        os.environ['MQTT_BRIDGE_CERT_DIR'] = cert_dir
        os.environ['MQTT_PASSWORD'] = 'pw'
        env_file = self.write('user.env', 'MQTT_USERNAME=alice\n')
        args = broker_args(load_settings(self.write('f.yaml', TLS_CONFIG.format(env_file=env_file))))
        self.assertEqual(args[:4], ['-h', 'secure-host', '-p', '8883'])
        self.assertIn('--cafile', args)
        self.assertIn('--insecure', args)
        self.assertEqual(args[args.index('-u') + 1], 'alice')
        self.assertEqual(args[args.index('-P') + 1], 'pw')

    def test_missing_config_falls_back_to_defaults(self):
        settings = load_settings(os.path.join(self.tmp.name, 'absent.yaml'))
        self.assertEqual(settings.address, 'localhost:1883')
        self.assertIsNone(settings.config_path)

    def test_as_bool_accepts_string_flags(self):
        self.assertTrue(as_bool('1'))
        self.assertTrue(as_bool('TRUE'))
        self.assertFalse(as_bool('0'))
        self.assertFalse(as_bool(''))

    def test_reason_text_handles_paho_reason_codes(self):
        from paho.mqtt.packettypes import PacketTypes
        from paho.mqtt.reasoncodes import ReasonCode
        text = reason_text(ReasonCode(PacketTypes.CONNACK, 'Not authorized'))
        self.assertIn('Not authorized', text)
        self.assertIn('135', text)
        self.assertIn('7', reason_text(7))


class TlsProbeTestCase(unittest.TestCase):
    def test_plaintext_listener_is_not_tls(self):
        import socket
        import threading
        server = socket.socket()
        server.bind(('127.0.0.1', 0))
        server.listen(1)
        self.addCleanup(server.close)
        threading.Thread(target=lambda: server.accept(), daemon=True).start()
        self.assertIs(port_speaks_tls('127.0.0.1', server.getsockname()[1], timeout=2), False)

    def test_closed_port_is_unreachable(self):
        import socket
        probe = socket.socket()
        probe.bind(('127.0.0.1', 0))
        port = probe.getsockname()[1]
        probe.close()
        self.assertIsNone(port_speaks_tls('127.0.0.1', port, timeout=2))


if __name__ == '__main__':
    unittest.main()
