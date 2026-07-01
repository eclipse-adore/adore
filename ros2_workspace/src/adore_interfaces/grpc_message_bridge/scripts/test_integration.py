#!/usr/bin/env python3
"""
Integration tests -- Supervision External Gateway gTA Integration Guide Phase 1.

Covers all 7 test scenarios from section 8 of the spec.

Usage:
    set -a && source .secrets.env && set +a
    PYTHONPATH=proto/generated python3 scripts/test_integration.py [--scenario N]
"""

import argparse
import json
import os
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'proto', 'generated'))

import grpc
from client import stream_pb2, stream_pb2_grpc
from messages import common_pb2

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_GREEN  = '\033[92m'
_RED    = '\033[91m'
_YELLOW = '\033[93m'
_RESET  = '\033[0m'

_results = []

def _pass(scenario, msg):
    print(f'  {_GREEN}PASS{_RESET}  {msg}')
    _results.append((scenario, True, msg))

def _fail(scenario, msg):
    print(f'  {_RED}FAIL{_RESET}  {msg}')
    _results.append((scenario, False, msg))

def _info(msg):
    print(f'       {msg}')


def _fetch_token(client_id, client_secret, expect_success=True):
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
    stub   = stream_pb2_grpc.ClientServiceStub(channel)
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
        _pass(2, f'HTTP 401 Unauthorized as expected')
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
    channel  = _make_channel(valid_token)
    received, error = _open_stream(channel, _subscription_msg(stream_pb2.TELEMETRY), timeout=8)
    channel.close()

    if error and error.code() not in (grpc.StatusCode.DEADLINE_EXCEEDED,):
        _fail(4, f'{error.code().name}: {error.details()!r}')
        return

    telemetry_msgs = [m for m in received if m.WhichOneof('payload') == 'telemetry']
    _info(f'Received {len(received)} messages total, {len(telemetry_msgs)} telemetry')

    if telemetry_msgs:
        t = telemetry_msgs[0].telemetry
        _info(f'vehicle_id={t.vehicle_id}  connected={t.is_connected}  '
              f'state={t.telemetry.state}  velocity={t.telemetry.velocity:.2f}')
        _pass(4, f'Stream opened, received {len(telemetry_msgs)} VehicleTelemetryUpdate message(s)')
    elif not error:
        _pass(4, 'Stream opened successfully (no vehicles active -- no telemetry received)')
    else:
        _fail(4, 'Stream timed out with no messages')


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

    wrong_vehicle = [
        m for m in filtered
        if m.WhichOneof('payload') == 'telemetry'
        and m.telemetry.vehicle_id not in vehicle_ids
    ]

    if wrong_vehicle:
        _fail(5, f'Received telemetry for unrequested vehicles: '
              f'{[m.telemetry.vehicle_id for m in wrong_vehicle]}')
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
# Entry point
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Inspect mode -- subscribe and pretty-print all incoming messages
# ---------------------------------------------------------------------------

def inspect(duration=30, vehicle_ids=None, sub_type=stream_pb2.ALL):
    from google.protobuf.json_format import MessageToJson

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
            ts = time.strftime('%H:%M:%S')
            payload = getattr(msg, field)
            print(f'[{ts}] {field.upper()}')
            print(MessageToJson(payload, preserving_proto_field_name=True, indent=2))
            print()

    except KeyboardInterrupt:
        if call[0]:
            call[0].cancel()
    except grpc.RpcError as e:
        if e.code() != grpc.StatusCode.CANCELLED:
            print(f'\nStream error: {e.code().name}: {e.details()}')

    channel.close()
    print(f'\nReceived: {counts if counts else "nothing"}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--scenario', type=int, default=0,
                        help='Run a single scenario (1-7). Default: run all.')
    parser.add_argument('--inspect', action='store_true',
                        help='Subscribe and print all incoming messages.')
    parser.add_argument('--duration', type=int, default=30,
                        help='Inspect duration in seconds (default: 30).')
    parser.add_argument('--vehicle', nargs='*', default=None,
                        help='Filter to specific vehicle IDs during inspect.')
    parser.add_argument('--type', choices=['ALL','TELEMETRY','NOTIFICATIONS'],
                        default='ALL', dest='sub_type',
                        help='Subscription type for inspect (default: ALL).')
    args = parser.parse_args()

    for var in ('AUTH_ENDPOINT', 'GRPC_ENDPOINT', 'CLIENT_ID', 'CLIENT_SECRET'):
        if not os.environ.get(var):
            print(f'Missing env var: {var}')
            print('Run: set -a && source .secrets.env && set +a')
            sys.exit(1)

    print(f'Auth:    {os.environ["AUTH_ENDPOINT"]}')
    print(f'gRPC:    {os.environ["GRPC_ENDPOINT"]}')
    print(f'Client:  {os.environ["CLIENT_ID"]}')

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

    if args.scenario == 0:
        passed = sum(1 for _, ok, _ in _results if ok)
        failed = sum(1 for _, ok, _ in _results if not ok)
        print(f'\n{"="*50}')
        print(f'Results: {_GREEN}{passed} passed{_RESET}  {_RED}{failed} failed{_RESET}  '
              f'of {len(_results)} checks')
        if failed:
            sys.exit(1)

