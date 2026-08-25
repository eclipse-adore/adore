"""Connection failure diagnostics.

Imports nothing from rclpy or paho so it can be used by the node and by the
standalone scripts alike.
"""
import socket
import ssl

AUTH_FAILURE_CODES = (4, 5, 134, 135)


def reason_text(reason_code) -> str:
    """paho 2.x hands back a ReasonCode object, which has no __int__."""
    name = getattr(reason_code, 'getName', None)
    value = getattr(reason_code, 'value', reason_code)
    return f'{name() if name else reason_code} (code {value})'


def is_auth_failure(reason_code) -> bool:
    return getattr(reason_code, 'value', reason_code) in AUTH_FAILURE_CODES


def port_speaks_tls(host: str, port: int, timeout: float = 3.0) -> bool | None:
    """True if the port completes a TLS handshake, False if it is plaintext,
    None if the TCP connection could not be established at all."""
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    try:
        raw = socket.create_connection((host, port), timeout=timeout)
    except OSError:
        return None
    with raw:
        try:
            with context.wrap_socket(raw):
                return True
        except OSError:
            return False


def failure_hints(host: str, port: int, tls_enabled: bool, missing_files=()) -> list:
    """Actionable lines explaining why a connection to host:port did not work."""
    address = f'{host}:{port}'
    hints = []
    if missing_files:
        hints.append(f'TLS material missing on disk: {", ".join(missing_files)}')
        hints.append('set MQTT_BRIDGE_CERT_DIR or correct the paths under mqtt.tls')

    speaks_tls = port_speaks_tls(host, port)
    if speaks_tls is None:
        hints.append(f'{address} refused a plain TCP probe; check the host, port and firewall')
    elif speaks_tls and not tls_enabled:
        hints.append(f'{address} speaks TLS but this client connected in plaintext, so the broker '
                     f'response decodes as garbage; enable mqtt.tls or set MQTT_TLS=1')
    elif not speaks_tls and tls_enabled:
        hints.append(f'{address} is a plaintext listener but this client attempted TLS; set MQTT_TLS=0')
    else:
        hints.append(f'{address} accepted a transport-level connection, so the failure is above '
                     f'the transport: credentials, client certificate or broker ACL')
    return hints
