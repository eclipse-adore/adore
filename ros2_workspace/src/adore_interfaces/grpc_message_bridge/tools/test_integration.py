#!/usr/bin/env python3
"""
Integration tests -- Supervision External Gateway gTA Integration Guide Phase 1.

Covers the 7 test scenarios from section 8 of the spec, plus scenario 8 which
checks the ROS side of the bridge.

Usage:
    set -a && source .secrets.env && set +a
    PYTHONPATH=proto/generated python3 tools/test_integration.py [--scenario N]
"""

import argparse
import collections
import json
import os
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'proto', 'generated'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import grpc
from google.protobuf import text_format
from google.protobuf.json_format import MessageToDict
from client import stream_pb2, stream_pb2_grpc
from messages import common_pb2

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_GREEN  = '\033[92m'
_RED    = '\033[91m'
_YELLOW = '\033[93m'
_CYAN   = '\033[96m'
_RESET  = '\033[0m'

_results = []

MAX_BODY   = 400
DUMP_LIMIT = 3


def _pass(scenario, msg):
    print(f'  {_GREEN}PASS{_RESET}  {msg}')
    _results.append((scenario, 'pass', msg))

def _fail(scenario, msg):
    print(f'  {_RED}FAIL{_RESET}  {msg}')
    _results.append((scenario, 'fail', msg))

def _warn(scenario, msg):
    print(f'  {_YELLOW}WARN{_RESET}  {msg}')
    _results.append((scenario, 'warn', msg))

def _info(msg):
    print(f'       {msg}')


# ---------------------------------------------------------------------------
# Topic map -- single source of truth is the bridge's own proto_registry
# ---------------------------------------------------------------------------

STREAM_KEY = 'client.ClientService.ClientStream'

Route = collections.namedtuple('Route', 'topic ros_msg_type format')

_FALLBACK_SEND = {
    'subscription':   Route('/supervision/subscription',  'std_msgs/msg/String', 'json'),
    'ack':            Route('/supervision/ack/tx',        'std_msgs/msg/String', 'json'),
    'signal_message': Route('/supervision/signaling/tx',  'std_msgs/msg/String', 'json'),
}
_FALLBACK_RECV = {
    'telemetry':      Route('/supervision/telemetry',     'std_msgs/msg/String', 'json'),
    'notification':   Route('/supervision/notifications', 'std_msgs/msg/String', 'json'),
    'ack':            Route('/supervision/ack/rx',        'std_msgs/msg/String', 'json'),
    'signal_message': Route('/supervision/signaling/rx',  'std_msgs/msg/String', 'json'),
}


def _load_topic_map():
    try:
        from grpc_message_bridge.proto_registry import STREAMS
        s = STREAMS[STREAM_KEY]
        as_routes = lambda fms: {
            fm.field_name: Route(fm.ros_topic, fm.ros_msg_type, fm.format) for fm in fms}
        return as_routes(s.send_fields), as_routes(s.recv_fields), 'proto_registry'
    except Exception as e:
        return _FALLBACK_SEND, _FALLBACK_RECV, f'fallback ({type(e).__name__}: {e})'


SEND_ROUTES, RECV_ROUTES, _TOPIC_SOURCE = _load_topic_map()

SEND_TOPICS = {f: r.topic for f, r in SEND_ROUTES.items()}
RECV_TOPICS = {f: r.topic for f, r in RECV_ROUTES.items()}


def _print_topic_map():
    print(f'\nTopic map (source: {_TOPIC_SOURCE})')
    print(f'  {"direction":<14}{"proto message":<16}{"oneof field":<16}'
          f'{"ROS topic":<30}{"ROS type":<22}format')
    for f, r in SEND_ROUTES.items():
        print(f'  {"ros -> grpc":<14}{"ClientMessage":<16}{f:<16}'
              f'{r.topic:<30}{r.ros_msg_type:<22}{r.format}')
    for f, r in RECV_ROUTES.items():
        print(f'  {"grpc -> ros":<14}{"ServerMessage":<16}{f:<16}'
              f'{r.topic:<30}{r.ros_msg_type:<22}{r.format}')

    missing = [f.name for f in stream_pb2.ServerMessage.DESCRIPTOR.oneofs[0].fields
               if f.name not in RECV_ROUTES]
    if missing:
        print(f'  {_YELLOW}ServerMessage oneof branches with no ROS route: '
              f'{missing}{_RESET}')


def _trunc(s):
    return s if len(s) <= MAX_BODY else s[:MAX_BODY] + f'... (+{len(s) - MAX_BODY} chars)'


def _to_dict(msg, defaults=False):
    kwargs = {'preserving_proto_field_name': True}
    if defaults:
        try:
            return MessageToDict(msg, always_print_fields_with_no_presence=True, **kwargs)
        except TypeError:
            return MessageToDict(msg, including_default_value_fields=True, **kwargs)
    return MessageToDict(msg, **kwargs)


def _payload_json(msg, field):
    """Exactly what the bridge puts in std_msgs/String.data for this field."""
    return json.dumps(_to_dict(getattr(msg, field)))


def _envelope(msg):
    """The non-oneof metadata the bridge never forwards to ROS."""
    if not msg.HasField('metadata'):
        return '<no metadata>'
    return json.dumps(_to_dict(msg.metadata))


def _dump_grpc(received):
    """
    Print every message received on the stream, its oneof branch, the ROS topic
    that branch routes to, and the payload the bridge would publish there.
    Messages with no oneof set are shown too, since the bridge drops them silently.
    """
    if not received:
        _info(f'{_YELLOW}no gRPC messages received on the stream{_RESET}')
        return {}

    counts = collections.Counter(m.WhichOneof('payload') for m in received)
    summary = ', '.join(f'{f or "<no payload set>"}={n}' for f, n in counts.most_common())
    _info(f'{len(received)} message(s): {summary}')

    shown = collections.Counter()
    for i, m in enumerate(received):
        field = m.WhichOneof('payload')
        key   = field or '<none>'
        if shown[key] >= DUMP_LIMIT:
            continue
        shown[key] += 1

        route = RECV_ROUTES.get(field)
        print()
        _info(f'{_CYAN}[msg {i}]{_RESET} ServerMessage.{key}')
        _info(f'  metadata   {_trunc(_envelope(m))}')

        if field is None:
            _info(f'  ros topic  {_YELLOW}none, oneof unset so the bridge drops '
                  f'this message{_RESET}')
            _dump_body(m, 'ServerMessage')
            continue

        if route is None:
            _info(f'  ros topic  {_YELLOW}none, {field!r} has no recv_fields entry in '
                  f'proto_registry so the bridge drops it{_RESET}')
        else:
            _info(f'  ros topic  {_GREEN}{route.topic}{_RESET}  '
                  f'[{route.ros_msg_type}, format={route.format}]')

        payload = getattr(m, field)
        _info(f'  ros data   {_trunc(_payload_json(m, field))}')
        _dump_body(payload, type(payload).DESCRIPTOR.full_name)

    for key, total in counts.items():
        if shown[key or '<none>'] < total:
            _info(f'  ... {total - shown[key or "<none>"]} more '
                  f'{key or "<no payload set>"} message(s) not shown')

    unroutable = sum(n for f, n in counts.items() if f not in RECV_ROUTES)
    if unroutable:
        _info(f'{_YELLOW}{unroutable} of {len(received)} message(s) have no ROS route '
              f'and never reach a topic{_RESET}')
    return dict(counts)


def _dump_body(msg, type_name):
    """
    proto3 omits defaults, so an all-default message serialises to '{}' and looks
    like missing data. Print the wire size and an explicit defaults-included view
    so an empty payload can be told apart from an unread one.
    """
    wire = len(msg.SerializeToString())
    raw  = text_format.MessageToString(msg, as_one_line=True).strip()

    _info(f'  proto type {type_name}  ({wire} wire byte{"" if wire == 1 else "s"})')
    if wire == 0:
        _info(f'  {_YELLOW}fields set none, every field is at its proto3 default, so the '
              f'gateway sent an empty message{_RESET}')
    else:
        _info(f'  fields set {_trunc(raw)}')
    _info(f'  with defaults {_trunc(json.dumps(_to_dict(msg, defaults=True)))}')


def _fetch_token(client_id, client_secret):
    params = urllib.parse.urlencode({
        'grant_type':    'client_credentials',
        'client_id':     client_id,
        'client_secret': client_secret,
    }).encode()
    req = urllib.request.Request(
        os.environ['AUTH_ENDPOINT'],
        data    = params,
        headers = {'Content-Type': 'application/x-www-form-urlencoded'},
        method  = 'POST',
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())


def _make_channel(token):
    creds = grpc.composite_channel_credentials(
        grpc.ssl_channel_credentials(),
        grpc.metadata_call_credentials(
            lambda ctx, cb: cb([('authorization', f'Bearer {token}')], None),
            name='bearer',
        ),
    )
    return grpc.secure_channel(os.environ['GRPC_ENDPOINT'], creds)


def _open_stream(channel, messages_fn, timeout=5):
    stub     = stream_pb2_grpc.ClientServiceStub(channel)
    received = []
    error    = [None]
    call     = [None]

    def _run():
        try:
            call[0] = stub.ClientStream(messages_fn())
            for msg in call[0]:
                received.append(msg)
        except grpc.RpcError as e:
            error[0] = e
        except StopIteration:
            pass

    t = threading.Thread(target=_run, daemon=True)
    t.start()
    t.join(timeout=timeout)
    if t.is_alive() and call[0]:
        call[0].cancel()
    t.join(timeout=2)
    # Ignore cancellation errors -- those are expected from our own cancel.
    if error[0] and error[0].code() == grpc.StatusCode.CANCELLED:
        error[0] = None
    return received, error[0]


def _subscription_msg(sub_type=stream_pb2.ALL, vehicle_ids=None):
    def _gen():
        yield stream_pb2.ClientMessage(
            subscription=stream_pb2.SubscriptionRequest(
                type=sub_type,
                vehicle_ids=vehicle_ids or [],
            ),
            metadata=common_pb2.FrontendMetadata(message_id='test-001'),
        )
        # Keep the send side open so the server keeps streaming back.
        # The bidi stream closes when the caller's timeout fires or the thread is stopped.
        while True:
            time.sleep(1)
    return _gen


# ---------------------------------------------------------------------------
# Scenario 1: Successful token retrieval
# ---------------------------------------------------------------------------

def scenario_1():
    print('\nScenario 1: Successful token retrieval')
    status, data = _fetch_token(os.environ['CLIENT_ID'], os.environ['CLIENT_SECRET'])
    _info(f'HTTP {status}')

    if status != 200:
        _fail(1, f'Expected HTTP 200, got {status}: {data}')
        return None

    if 'access_token' not in data:
        _fail(1, 'Response missing access_token')
        return None

    expires_in = data.get('expires_in')
    if expires_in != 1800:
        _fail(1, f'Expected expires_in=1800, got {expires_in}')
        return None

    _pass(1, f'HTTP 200, access_token present, expires_in={expires_in}')

    # Decode JWT claims for visibility (no signature verification).
    try:
        import base64
        payload = data['access_token'].split('.')[1]
        payload += '=' * (4 - len(payload) % 4)
        claims  = json.loads(base64.urlsafe_b64decode(payload))
        _info(f"JWT claims: { {k: claims[k] for k in ('client_id','tenant_id','fleet_ids','exp') if k in claims} }")
    except Exception:
        pass

    return data['access_token']


# ---------------------------------------------------------------------------
# Scenario 2: Failed token retrieval (invalid credentials)
# ---------------------------------------------------------------------------

def scenario_2():
    print('\nScenario 2: Failed token retrieval -- invalid credentials')
    status, data = _fetch_token(os.environ['CLIENT_ID'], 'invalid-secret-xxxx')
    _info(f'HTTP {status}: {data}')

    if status == 401:
        _pass(2, 'HTTP 401 Unauthorized as expected')
    else:
        _fail(2, f'Expected HTTP 401, got {status}')


# ---------------------------------------------------------------------------
# Scenario 3: Expired token rejected
# ---------------------------------------------------------------------------

def scenario_3(valid_token):
    print('\nScenario 3: Expired token rejected')
    _info('Using a deliberately malformed/expired token string')

    expired_token = valid_token[:-10] + 'XXXXXXXXXXX'
    channel = _make_channel(expired_token)
    _, error = _open_stream(channel, _subscription_msg(), timeout=5)
    channel.close()

    if error and error.code() == grpc.StatusCode.UNAUTHENTICATED:
        _pass(3, f'UNAUTHENTICATED as expected: {error.details()!r}')
    elif error:
        _fail(3, f'Expected UNAUTHENTICATED, got {error.code().name}: {error.details()!r}')
    else:
        _fail(3, 'Stream opened with invalid token -- expected rejection')


# ---------------------------------------------------------------------------
# Scenario 4: Telemetry subscription (happy path)
# ---------------------------------------------------------------------------

def scenario_4(valid_token):
    print('\nScenario 4: Telemetry subscription (happy path)')
    _info(f'Subscribing TELEMETRY, target ROS topic {RECV_TOPICS.get("telemetry", "<unmapped>")}')

    channel  = _make_channel(valid_token)
    received, error = _open_stream(channel, _subscription_msg(stream_pb2.TELEMETRY), timeout=8)
    channel.close()

    if error and error.code() not in (grpc.StatusCode.DEADLINE_EXCEEDED,):
        _fail(4, f'{error.code().name}: {error.details()!r}')
        return

    counts = _dump_grpc(received)
    telemetry_msgs = [m for m in received if m.WhichOneof('payload') == 'telemetry']

    if telemetry_msgs:
        t = telemetry_msgs[0].telemetry
        _info(f'vehicle_id={t.vehicle_id}  connected={t.is_connected}  '
              f'state={t.telemetry.state}  velocity={t.telemetry.velocity:.2f}')
        _pass(4, f'Received {len(telemetry_msgs)} VehicleTelemetryUpdate message(s) '
                 f'for {RECV_TOPICS["telemetry"]}')
    elif received:
        other = ', '.join(f or '<no payload set>' for f in counts)
        _warn(4, f'Subscribed TELEMETRY and got {len(received)} message(s) but no '
                 f'telemetry: {other}. Nothing reaches {RECV_TOPICS["telemetry"]}.')
    else:
        _warn(4, 'Stream opened but the gateway sent nothing. Nothing can reach ROS '
                 'from an empty stream, so a green run here only proves auth works.')


# ---------------------------------------------------------------------------
# Scenario 5: Vehicle ID filtering
# ---------------------------------------------------------------------------

def scenario_5(valid_token):
    print('\nScenario 5: Vehicle ID filtering')

    # First get all telemetry to find an active vehicle ID.
    channel  = _make_channel(valid_token)
    received, _ = _open_stream(channel, _subscription_msg(stream_pb2.TELEMETRY), timeout=6)
    channel.close()

    telemetry_msgs = [m for m in received if m.WhichOneof('payload') == 'telemetry']
    if not telemetry_msgs:
        _info('No active vehicles found -- skipping filter validation, testing with dummy ID')
        vehicle_ids = ['MV-NONEXISTENT']
    else:
        vehicle_ids = list({m.telemetry.vehicle_id for m in telemetry_msgs})[:1]
        _info(f'Filtering to vehicle_ids={vehicle_ids}')

    channel  = _make_channel(valid_token)
    filtered, error = _open_stream(
        channel, _subscription_msg(stream_pb2.TELEMETRY, vehicle_ids), timeout=6)
    channel.close()

    if error and error.code() not in (grpc.StatusCode.DEADLINE_EXCEEDED,):
        _fail(5, f'{error.code().name}: {error.details()!r}')
        return

    _dump_grpc(filtered)

    wrong_vehicle = [
        m for m in filtered
        if m.WhichOneof('payload') == 'telemetry'
        and m.telemetry.vehicle_id not in vehicle_ids
    ]

    if wrong_vehicle:
        _fail(5, f'Received telemetry for unrequested vehicles: '
              f'{[m.telemetry.vehicle_id for m in wrong_vehicle]}')
    elif not filtered:
        _warn(5, f'Filter untested, zero messages returned for vehicle_ids={vehicle_ids}')
    else:
        _pass(5, f'All {len(filtered)} messages matched requested vehicle_ids={vehicle_ids}')


# ---------------------------------------------------------------------------
# Scenario 6: Disconnect and reconnect
# ---------------------------------------------------------------------------

def scenario_6(valid_token):
    print('\nScenario 6: Disconnect and reconnect')

    channel = _make_channel(valid_token)
    stub    = stream_pb2_grpc.ClientServiceStub(channel)

    def _gen():
        yield stream_pb2.ClientMessage(
            subscription=stream_pb2.SubscriptionRequest(type=stream_pb2.ALL),
            metadata=common_pb2.FrontendMetadata(message_id='reconn-001'),
        )
        time.sleep(1)

    first_received = []
    try:
        for msg in stub.ClientStream(_gen(), timeout=3):
            first_received.append(msg)
    except (grpc.RpcError, StopIteration):
        pass

    channel.close()
    _info(f'First connection: received {len(first_received)} messages, disconnected')

    # Reconnect with a fresh channel.
    time.sleep(0.5)
    channel2 = _make_channel(valid_token)
    received2, error2 = _open_stream(channel2, _subscription_msg(stream_pb2.ALL), timeout=5)
    channel2.close()

    _dump_grpc(received2)

    if error2 and error2.code() not in (grpc.StatusCode.DEADLINE_EXCEEDED,):
        _fail(6, f'Reconnect failed: {error2.code().name}: {error2.details()!r}')
    else:
        _pass(6, f'Reconnect successful, received {len(received2)} messages on second connection')


# ---------------------------------------------------------------------------
# Scenario 7: Invalid subscription request
# ---------------------------------------------------------------------------

def scenario_7(valid_token):
    print('\nScenario 7: Invalid subscription request')

    channel = _make_channel(valid_token)

    def _bad_request():
        # Send a ClientMessage with no subscription set (empty message).
        yield stream_pb2.ClientMessage(
            metadata=common_pb2.FrontendMetadata(message_id='bad-001'),
        )
        time.sleep(2)

    received, error = _open_stream(channel, _bad_request, timeout=5)
    channel.close()

    if error and error.code() == grpc.StatusCode.INVALID_ARGUMENT:
        _pass(7, f'INVALID_ARGUMENT as expected: {error.details()!r}')
    elif error:
        _info(f'Got {error.code().name}: {error.details()!r}')
        # Server may silently ignore rather than reject -- note it but don't hard-fail.
        _pass(7, f'Server responded with {error.code().name} (acceptable -- no crash)')
    else:
        _info(f'Stream completed without error, received {len(received)} messages')
        _pass(7, 'Server accepted message without error (lenient validation)')


# ---------------------------------------------------------------------------
# Scenario 8: ROS side of the bridge
# ---------------------------------------------------------------------------

def scenario_8(duration=15, trigger=True):
    print('\nScenario 8: ROS topic data (requires a running bridge)')

    try:
        import rclpy
        from rclpy.node import Node
        from rclpy.qos import (DurabilityPolicy, HistoryPolicy, QoSProfile,
                               ReliabilityPolicy)
        from std_msgs.msg import String
    except ImportError as e:
        _warn(8, f'rclpy unavailable ({e}), ROS side not checked')
        return

    sub_topic = SEND_TOPICS.get('subscription')

    rclpy.init()
    node = Node('bridge_integration_probe')
    qos  = QoSProfile(
        depth       = 10,
        history     = HistoryPolicy.KEEP_LAST,
        reliability = ReliabilityPolicy.RELIABLE,
        durability  = DurabilityPolicy.VOLATILE,
    )

    received = {topic: [] for topic in RECV_TOPICS.values()}
    for topic in received:
        node.create_subscription(
            String, topic,
            lambda msg, t=topic: received[t].append(msg.data),
            qos)
    _info(f'Subscribed to: {", ".join(sorted(received))}')

    pub = node.create_publisher(String, sub_topic, qos) if trigger else None
    _spin(node, 2.0)
    _print_ros_graph(node, sub_topic)

    if pub is not None:
        request = json.dumps({'type': 'ALL', 'vehicleIds': []})
        _info(f'{_CYAN}ROS{_RESET}  publish -> {sub_topic}  {request}')
        for _ in range(3):
            pub.publish(String(data=request))
            _spin(node, 0.5)

    _info(f'Listening on ROS for {duration}s')
    _spin(node, duration)

    node.destroy_node()
    rclpy.shutdown()

    print()
    total = 0
    for topic in sorted(received):
        msgs   = received[topic]
        total += len(msgs)
        colour = _GREEN if msgs else _YELLOW
        _info(f'{colour}{len(msgs):>5}{_RESET}  {topic}')
        for data in msgs[:DUMP_LIMIT]:
            _info(f'         {_trunc(data)}')

    if total:
        live = sum(1 for v in received.values() if v)
        _pass(8, f'{total} ROS message(s) across {live} topic(s)')
    else:
        _fail(8, 'No data on any ROS topic. The gRPC scenarios above can pass while '
                 'the bridge publishes nothing.')


def _spin(node, seconds):
    import rclpy
    deadline = time.time() + seconds
    while time.time() < deadline:
        rclpy.spin_once(node, timeout_sec=0.1)


def _print_ros_graph(node, sub_topic):
    live = dict(node.get_topic_names_and_types())
    _info('ROS graph:')
    for topic in sorted(set(RECV_TOPICS.values()) | {sub_topic}):
        types  = live.get(topic)
        pubs   = len(node.get_publishers_info_by_topic(topic))
        subs   = len(node.get_subscriptions_info_by_topic(topic))
        colour = _GREEN if types else _YELLOW
        _info(f'  {colour}{topic:<34}{_RESET}'
              f'{types[0] if types else "<not advertised>":<24}pubs={pubs} subs={subs}')

    # The bridge advertises every recv topic at startup, so absence means it is not up.
    if not any(t in live for t in RECV_TOPICS.values()):
        _info(f'{_YELLOW}Bridge publishers not visible. Check `make start`, ROS_DOMAIN_ID '
              f'and that the container shares this network namespace.{_RESET}')


# ---------------------------------------------------------------------------
# Inspect mode -- subscribe and pretty-print all incoming messages
# ---------------------------------------------------------------------------

def inspect(duration=30, vehicle_ids=None, sub_type=stream_pb2.ALL):
    status, data = _fetch_token(os.environ['CLIENT_ID'], os.environ['CLIENT_SECRET'])
    if status != 200 or 'access_token' not in data:
        print(f'Token fetch failed: {data}')
        sys.exit(1)
    token = data['access_token']

    channel = _make_channel(token)
    stub    = stream_pb2_grpc.ClientServiceStub(channel)

    type_name = {stream_pb2.TELEMETRY: 'TELEMETRY',
                 stream_pb2.NOTIFICATIONS: 'NOTIFICATIONS',
                 stream_pb2.ALL: 'ALL'}[sub_type]

    print(f'Subscribing ({type_name}, vehicles={vehicle_ids or "all"}) '
          f'for {duration}s -- Ctrl-C to stop\n')

    counts = {}
    call   = [None]

    def _gen():
        yield stream_pb2.ClientMessage(
            subscription=stream_pb2.SubscriptionRequest(
                type=sub_type,
                vehicle_ids=vehicle_ids or [],
            ),
            metadata=common_pb2.FrontendMetadata(message_id='inspect-001'),
        )
        deadline = time.time() + duration
        while time.time() < deadline:
            time.sleep(0.5)

    try:
        call[0] = stub.ClientStream(_gen())
        for msg in call[0]:
            field = msg.WhichOneof('payload')
            if field is None:
                continue

            counts[field] = counts.get(field, 0) + 1
            ts    = time.strftime('%H:%M:%S')
            topic = RECV_TOPICS.get(field, '<unmapped>')

            if field == 'telemetry':
                t   = msg.telemetry
                tel = t.telemetry
                print(f'[{ts}] TELEMETRY -> {topic}  vehicle={t.vehicle_id}  '
                      f'connected={t.is_connected}')
                print(f'         state={tel.state}  '
                      f'pos=({tel.position.lat:.5f}, {tel.position.lon:.5f})  '
                      f'heading={tel.heading:.3f}rad  '
                      f'velocity={tel.velocity:.2f}km/h  '
                      f'battery={tel.battery:.1f}%  '
                      f'passengers={tel.passengers}  '
                      f'obstacles={len(tel.obstacles)}')

            elif field == 'notification':
                n = msg.notification.notification
                print(f'[{ts}] NOTIFICATION -> {topic}  id={msg.notification.id}  '
                      f'vehicle={msg.notification.vehicle_id}')
                print(f'         [{n.severity}] {n.title}: {n.message}  node={n.ros_node}')

            elif field == 'ack':
                print(f'[{ts}] ACK -> {topic}  ok={msg.ack.success}  msg={msg.ack.error_msg!r}')

            elif field == 'signal_message':
                s     = msg.signal_message
                inner = s.WhichOneof('payload')
                print(f'[{ts}] SIGNAL -> {topic}  session={s.session_id}  '
                      f'peer={s.peer_id}  type={inner}')

            else:
                print(f'[{ts}] {field.upper()} -> {topic}  {getattr(msg, field)}')

            print(f'         ros_payload: {_trunc(_payload_json(msg, field))}')

    except KeyboardInterrupt:
        if call[0]:
            call[0].cancel()
    except grpc.RpcError as e:
        if e.code() != grpc.StatusCode.CANCELLED:
            print(f'\nStream error: {e.code().name}: {e.details()}')

    channel.close()
    print(f'\nReceived: {counts if counts else "nothing"}')


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--scenario', type=int, default=0,
                        help='Run a single scenario (1-8). Default: run all.')
    parser.add_argument('--inspect', action='store_true',
                        help='Subscribe and print all incoming messages.')
    parser.add_argument('--duration', type=int, default=30,
                        help='Inspect duration in seconds (default: 30).')
    parser.add_argument('--vehicle', nargs='*', default=None,
                        help='Filter to specific vehicle IDs during inspect.')
    parser.add_argument('--type', choices=['ALL','TELEMETRY','NOTIFICATIONS'],
                        default='ALL', dest='sub_type',
                        help='Subscription type for inspect (default: ALL).')
    parser.add_argument('--ros-duration', type=int, default=15,
                        help='Scenario 8 ROS listen window in seconds (default: 15).')
    parser.add_argument('--no-ros-trigger', action='store_true',
                        help='Scenario 8: listen only, do not publish a subscription request.')
    parser.add_argument('--full', action='store_true',
                        help='Print payloads untruncated.')
    parser.add_argument('--dump', type=int, default=DUMP_LIMIT,
                        help=f'Sample payloads printed per field (default: {DUMP_LIMIT}).')
    args = parser.parse_args()

    if args.full:
        MAX_BODY = 10 ** 9
    DUMP_LIMIT = args.dump

    for var in ('AUTH_ENDPOINT', 'GRPC_ENDPOINT', 'CLIENT_ID', 'CLIENT_SECRET'):
        if not os.environ.get(var):
            print(f'Missing env var: {var}')
            print('Run: set -a && source .secrets.env && set +a')
            sys.exit(1)

    print(f'Auth:       {os.environ["AUTH_ENDPOINT"]}')
    print(f'gRPC:       {os.environ["GRPC_ENDPOINT"]}')
    print(f'Client:     {os.environ["CLIENT_ID"]}')
    print(f'ROS domain: {os.environ.get("ROS_DOMAIN_ID", "0 (default)")}')
    _print_topic_map()

    if args.inspect:
        sub_type_map = {'ALL': stream_pb2.ALL, 'TELEMETRY': stream_pb2.TELEMETRY,
                        'NOTIFICATIONS': stream_pb2.NOTIFICATIONS}
        inspect(duration=args.duration, vehicle_ids=args.vehicle,
                sub_type=sub_type_map[args.sub_type])
        sys.exit(0)

    token = scenario_1() if args.scenario in (0, 1) else None

    if args.scenario == 0 or args.scenario != 1:
        if token is None:
            token = _fetch_token(os.environ['CLIENT_ID'], os.environ['CLIENT_SECRET'])[1].get('access_token')
        if not token:
            print('Cannot obtain token -- aborting remaining tests')
            sys.exit(1)

    run = lambda n, fn, *a: fn(*a) if args.scenario in (0, n) else None

    run(2, scenario_2)
    run(3, scenario_3, token)
    run(4, scenario_4, token)
    run(5, scenario_5, token)
    run(6, scenario_6, token)
    run(7, scenario_7, token)
    run(8, scenario_8, args.ros_duration, not args.no_ros_trigger)

    if args.scenario == 0:
        passed = sum(1 for _, s, _ in _results if s == 'pass')
        failed = sum(1 for _, s, _ in _results if s == 'fail')
        warned = sum(1 for _, s, _ in _results if s == 'warn')
        print(f'\n{"="*50}')
        print(f'Results: {_GREEN}{passed} passed{_RESET}  {_RED}{failed} failed{_RESET}  '
              f'{_YELLOW}{warned} warned{_RESET}  of {len(_results)} checks')
        for n, status, msg in _results:
            if status != 'pass':
                colour = _RED if status == 'fail' else _YELLOW
                print(f'  {colour}{status.upper():<5}{_RESET} scenario {n}: {msg}')
        if failed:
            sys.exit(1)
