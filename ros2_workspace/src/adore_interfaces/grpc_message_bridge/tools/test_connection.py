#!/usr/bin/env python3
"""
Standalone connection test -- no ROS required.

Tests in order:
  1. OAuth2 token fetch
  2. TLS + auth gRPC channel establishment
  3. VehicleStream handshake (sends one heartbeat, waits for any response)
  4. ClientStream handshake (sends subscription request, waits for any response)

Usage:
    # From the project root:
    PYTHONPATH=proto/generated python3 scripts/test_connection.py

    # Or with explicit secrets:
    AUTH_ENDPOINT=https://... CLIENT_ID=... CLIENT_SECRET=... TENANT_ID=dlr \
    FLEET_IDS=fleet_100,fleet_101 GRPC_ENDPOINT=host:443 \
    PYTHONPATH=proto/generated python3 scripts/test_connection.py

    # Load from .secrets.env:
    set -a && source .secrets.env && set +a
    PYTHONPATH=proto/generated python3 scripts/test_connection.py
"""

import os
import sys
import time
import json
import threading
import urllib.request
import urllib.parse
import urllib.error

# ---------------------------------------------------------------------------
# Colour helpers
# ---------------------------------------------------------------------------
_GREEN  = '\033[92m'
_RED    = '\033[91m'
_YELLOW = '\033[93m'
_RESET  = '\033[0m'

def ok(msg):   print(f'  {_GREEN}✓{_RESET}  {msg}')
def fail(msg): print(f'  {_RED}✗{_RESET}  {msg}'); sys.exit(1)
def warn(msg): print(f'  {_YELLOW}!{_RESET}  {msg}')
def section(msg): print(f'\n{msg}')


# ---------------------------------------------------------------------------
# 1. Token fetch
# ---------------------------------------------------------------------------

def test_token_fetch(auth_endpoint, client_id, client_secret, tenant_id, fleet_ids):
    section('1. OAuth2 token fetch')

    params = {
        'grant_type':    'client_credentials',
        'client_id':     client_id,
        'client_secret': client_secret,
    }
    if tenant_id:
        params['tenant_id'] = tenant_id
    if fleet_ids:
        params['fleet_ids'] = ','.join(fleet_ids)

    print(f'     POST {auth_endpoint}')
    print(f'     client_id={client_id}  tenant_id={tenant_id}  fleet_ids={fleet_ids}')

    body = urllib.parse.urlencode(params).encode()
    req  = urllib.request.Request(
        auth_endpoint,
        data    = body,
        headers = {'Content-Type': 'application/x-www-form-urlencoded'},
        method  = 'POST',
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors='replace')
        fail(f'HTTP {e.code}: {body}')
    except Exception as e:
        fail(str(e))

    if 'access_token' not in data:
        fail(f'No access_token in response: {data}')

    token    = data['access_token']
    expires  = data.get('expires_in', '?')
    ok(f'Token received  expires_in={expires}s  token={token[:20]}...')

    # Decode JWT claims without verifying signature (for inspection only).
    try:
        import base64
        parts   = token.split('.')
        padding = 4 - len(parts[1]) % 4
        payload = base64.urlsafe_b64decode(parts[1] + '=' * padding)
        claims  = json.loads(payload)
        ok(f'JWT claims: {json.dumps({k: claims[k] for k in claims if k in ("sub","aud","exp","tenant_id","fleet_ids","scope")}, default=str)}')
    except Exception:
        warn('Could not decode JWT payload (not a JWT or unexpected format)')

    return token


# ---------------------------------------------------------------------------
# 2. gRPC channel
# ---------------------------------------------------------------------------

def test_channel(grpc_endpoint, token, tenant_id, fleet_ids):
    section('2. gRPC channel (TLS)')
    import grpc

    print(f'     {grpc_endpoint}')

    metadata = [
        ('authorization', f'Bearer {token}'),
    ]
    if tenant_id:
        metadata.append(('x-tenant-id', tenant_id))
    if fleet_ids:
        metadata.append(('x-fleet-ids', ','.join(fleet_ids)))

    tls_creds = grpc.ssl_channel_credentials()
    channel   = grpc.secure_channel(grpc_endpoint, tls_creds)

    try:
        grpc.channel_ready_future(channel).result(timeout=5)
        ok(f'Channel ready')
    except grpc.FutureTimeoutError:
        fail('Channel did not become ready within 5s -- check GRPC_ENDPOINT and network')

    return channel, metadata


# ---------------------------------------------------------------------------
# 3. VehicleStream
# ---------------------------------------------------------------------------

def test_vehicle_stream(channel, metadata):
    section('3. VehicleStream (vehicle.VehicleService)')
    import grpc
    from vehicle import stream_pb2, stream_pb2_grpc
    from messages import events_pb2, common_pb2

    stub = stream_pb2_grpc.VehicleServiceStub(channel)

    def _messages():
        yield stream_pb2.VehicleMessage(
            heartbeat = events_pb2.Heartbeat(status='test'),
            metadata  = common_pb2.MessageMetadata(
                message_id = 'test-001',
                vehicle_id = 'test-vehicle',
            ),
        )
        # Keep stream open briefly so the server has time to respond.
        time.sleep(2)

    received = []
    error    = [None]

    def _call():
        try:
            for msg in stub.VehicleStream(_messages(), metadata=metadata, timeout=5):
                received.append(msg)
        except grpc.RpcError as e:
            error[0] = e

    t = threading.Thread(target=_call)
    t.start()
    t.join(timeout=6)

    if error[0]:
        code = error[0].code()
        if code == grpc.StatusCode.UNIMPLEMENTED:
            warn('UNIMPLEMENTED -- service exists but VehicleStream not active on this endpoint')
        elif code == grpc.StatusCode.UNAUTHENTICATED:
            fail(f'UNAUTHENTICATED -- token or metadata headers rejected: {error[0].details()}')
        elif code == grpc.StatusCode.PERMISSION_DENIED:
            fail(f'PERMISSION_DENIED -- tenant/fleet not authorised: {error[0].details()}')
        else:
            warn(f'{code.name}: {error[0].details()}')
    else:
        ok(f'Stream opened successfully')

    if received:
        for msg in received:
            field = msg.WhichOneof('payload')
            ok(f'Received {field}: {getattr(msg, field)}')
    else:
        warn('No messages received (stream opened but server sent nothing -- may be normal)')


# ---------------------------------------------------------------------------
# 4. ClientStream
# ---------------------------------------------------------------------------

def test_client_stream(channel, metadata):
    section('4. ClientStream (client.ClientService)')
    import grpc
    from client import stream_pb2, stream_pb2_grpc
    from messages import common_pb2

    stub = stream_pb2_grpc.ClientServiceStub(channel)

    def _messages():
        yield stream_pb2.ClientMessage(
            subscription = stream_pb2.SubscriptionRequest(
                type        = stream_pb2.ALL,
                vehicle_ids = [],
            ),
            metadata = common_pb2.FrontendMetadata(message_id='test-sub-001'),
        )
        time.sleep(2)

    received = []
    error    = [None]

    def _call():
        try:
            for msg in stub.ClientStream(_messages(), metadata=metadata, timeout=5):
                received.append(msg)
        except grpc.RpcError as e:
            error[0] = e

    t = threading.Thread(target=_call)
    t.start()
    t.join(timeout=6)

    if error[0]:
        code = error[0].code()
        if code == grpc.StatusCode.UNIMPLEMENTED:
            warn('UNIMPLEMENTED -- ClientService not active on this endpoint')
        elif code == grpc.StatusCode.UNAUTHENTICATED:
            fail(f'UNAUTHENTICATED: {error[0].details()}')
        elif code == grpc.StatusCode.PERMISSION_DENIED:
            fail(f'PERMISSION_DENIED: {error[0].details()}')
        else:
            warn(f'{code.name}: {error[0].details()}')
    else:
        ok('Stream opened successfully')

    if received:
        for msg in received:
            field = msg.WhichOneof('payload')
            ok(f'Received {field}: {getattr(msg, field)}')
    else:
        warn('No messages received (may be normal if no vehicles are active)')


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    auth_endpoint = os.environ.get('AUTH_ENDPOINT', '')
    grpc_endpoint = os.environ.get('GRPC_ENDPOINT', '')
    client_id     = os.environ.get('CLIENT_ID', '')
    client_secret = os.environ.get('CLIENT_SECRET', '')
    tenant_id     = os.environ.get('TENANT_ID', '')
    fleet_ids     = [f.strip() for f in os.environ.get('FLEET_IDS', '').split(',') if f.strip()]

    missing = [k for k, v in {
        'AUTH_ENDPOINT': auth_endpoint,
        'GRPC_ENDPOINT': grpc_endpoint,
        'CLIENT_ID':     client_id,
        'CLIENT_SECRET': client_secret,
    }.items() if not v]

    if missing:
        print(f'Missing env vars: {", ".join(missing)}')
        print('Run:  set -a && source .secrets.env && set +a')
        sys.exit(1)

    print(f'Testing connection to {grpc_endpoint}')
    print(f'Auth: {auth_endpoint}')
    print(f'Tenant: {tenant_id}  Fleets: {fleet_ids}')

    token               = test_token_fetch(auth_endpoint, client_id, client_secret, tenant_id, fleet_ids)
    channel, metadata   = test_channel(grpc_endpoint, token, tenant_id, fleet_ids)
    test_vehicle_stream(channel, metadata)
    test_client_stream(channel, metadata)

    print(f'\n{_GREEN}Done.{_RESET}')
    channel.close()
