"""
TLS + OAuth2 client-credentials channel factory.

Spec: Supervision External Gateway gTA Integration Guide Phase 1
  - Token endpoint: POST /auth/token
  - Body: grant_type, client_id, client_secret only
  - Token TTL: 1800s (30 minutes)
  - gRPC auth: Authorization: Bearer <token>

Environment variables (via .secrets.env):
  GRPC_ENDPOINT    host:port  e.g. supervision.dev-motor-ai.com:443
  AUTH_ENDPOINT    full token URL e.g. https://supervision.dev-motor-ai.com/auth/token
  CLIENT_ID        OAuth2 client_id
  CLIENT_SECRET    OAuth2 client_secret
"""

import json
import logging
import os
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Optional

import grpc

log = logging.getLogger(__name__)

_TOKEN_REFRESH_BUFFER_S = 120  # refresh 2 min before 30-min TTL expires


class _OAuth2CallCredentials(grpc.AuthMetadataPlugin):
    def __init__(self, auth_endpoint: str, client_id: str, client_secret: str):
        self._endpoint     = auth_endpoint
        self._client_id    = client_id
        self._client_secret = client_secret
        self._token:      Optional[str] = None
        self._expires_at: float         = 0.0
        self._lock = threading.Lock()

    def _fetch(self) -> None:
        body = urllib.parse.urlencode({
            'grant_type':    'client_credentials',
            'client_id':     self._client_id,
            'client_secret': self._client_secret,
        }).encode()
        req = urllib.request.Request(
            self._endpoint,
            data    = body,
            headers = {'Content-Type': 'application/x-www-form-urlencoded'},
            method  = 'POST',
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read())
        except urllib.error.HTTPError as e:
            body = e.read().decode(errors='replace')
            raise RuntimeError(f'Token fetch HTTP {e.code}: {body}') from e

        if 'access_token' not in data:
            raise RuntimeError(f'Token response missing access_token: {data}')

        ttl = data.get('expires_in', 1800)
        self._token      = data['access_token']
        self._expires_at = time.monotonic() + ttl - _TOKEN_REFRESH_BUFFER_S
        log.info('OAuth2 token refreshed (expires_in=%ds)', ttl)

    def _ensure_valid_token(self) -> str:
        if self._token and time.monotonic() < self._expires_at:
            return self._token
        last_err = None
        for attempt in range(3):
            try:
                self._fetch()
                return self._token
            except Exception as e:
                last_err = e
                log.warning('Token fetch attempt %d/3 failed: %s', attempt + 1, e)
                if attempt < 2:
                    time.sleep(2 ** attempt)
        raise RuntimeError(f'Token fetch failed after 3 attempts: {last_err}')

    def __call__(self, context, callback):
        with self._lock:
            try:
                token = self._ensure_valid_token()
            except Exception as e:
                log.error('Cannot obtain OAuth2 token: %s', e)
                callback([], grpc.StatusCode.UNAUTHENTICATED)
                return
        callback([('authorization', f'Bearer {token}')], None)


def make_channel(address: Optional[str] = None) -> grpc.Channel:
    """
    Return a TLS+OAuth2 gRPC channel.
    Falls back to insecure for local dev when AUTH_ENDPOINT is unset.
    """
    addr          = address or os.environ.get('GRPC_ENDPOINT', '')
    auth_endpoint = os.environ.get('AUTH_ENDPOINT', '')
    client_id     = os.environ.get('CLIENT_ID', '')
    client_secret = os.environ.get('CLIENT_SECRET', '')

    if not addr:
        raise ValueError('No gRPC address: pass address or set GRPC_ENDPOINT')

    if auth_endpoint and client_id and client_secret:
        log.info('Creating TLS+OAuth2 channel to %s', addr)
        plugin     = _OAuth2CallCredentials(auth_endpoint, client_id, client_secret)
        tls_creds  = grpc.ssl_channel_credentials()
        call_creds = grpc.metadata_call_credentials(plugin, name='oauth2')
        creds      = grpc.composite_channel_credentials(tls_creds, call_creds)
        return grpc.secure_channel(addr, creds)

    log.warning('No auth credentials set -- using insecure channel to %s', addr)
    return grpc.insecure_channel(addr)
