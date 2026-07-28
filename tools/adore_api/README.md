# ADORe API

REST API for autonomous driving scenario management, model checking, data recording, and ROS2 system integration.

The ADORe REST API is automatically started with the ADORE CLI.
There is no need to manually start it.

> **⚠️ SECURITY WARNING:**
> The ADORe API starts ROS 2 launch files, which execute Python on the host.
> This system has **not** undergone a security audit and is intended
> **for research purposes only**.
> **Do not** expose it to the public internet or run it on any publicly accessible system.

`POST /api/scenario/start` runs launch files that already exist under the scenario directory.

To disable the ADORe API modify the `adore.env` file before launching the ADORE CLI


## Quick Start

```bash
# Start the API server
cd tools/adore_api
python adore_api.py

# Check status
curl http://localhost:8888/api/status
```

## Security configuration

All settings are read from the environment at startup.

| Variable | Default | Effect |
|---|---|---|
| `ADORE_API_HOST` | `127.0.0.1` | Bind address. Also settable with `--host`. Any non-loopback value exposes an interface that executes arbitrary code. |
| `ADORE_API_TOKEN` | unset | When set, every request must present the token. Anonymous access when unset. |
| `ADORE_API_CORS_ORIGINS` | unset | Comma-separated list of origins allowed to make cross-origin requests, e.g. `http://localhost:3000,http://localhost:5000`. Empty means same-origin only. |

### Authentication

With `ADORE_API_TOKEN` set, the token is accepted in any of these forms:

```bash
curl -H "Authorization: Bearer $ADORE_API_TOKEN" http://localhost:8888/api/status
curl -H "X-ADORE-API-Token: $ADORE_API_TOKEN" http://localhost:8888/api/status
```

For the browser UI, load `http://localhost:8888/?token=<token>` once. The server stores the
token in a `SameSite=Strict` HttpOnly cookie for subsequent requests. Requests without a valid
token return `401`.

### Cross-origin requests

The bundled Mission Control UI is served by this same application and needs no CORS
configuration. Add an origin to `ADORE_API_CORS_ORIGINS` only when a separately hosted
dashboard needs to call the API. State-changing requests carrying an `Origin` or `Referer`
outside that allowlist return `403`.

### Running in Docker

Under `--network host` the loopback default works unchanged. When publishing the port instead,
the server must bind all interfaces inside the container, so keep the published port on the
host loopback:

```bash
docker run -e ADORE_API_HOST=0.0.0.0 -p 127.0.0.1:8888:8888 ...
```

Binding the API to a routable address gives every peer on that network unauthenticated code
execution. If it is unavoidable, set `ADORE_API_TOKEN` and keep the network isolated.

## Documentation

- **[📖 API Reference](api_reference.md)** - Complete endpoint documentation with request/response schemas
- **[💻 cURL Examples](api_reference_curl_examples.md)** - Ready-to-use command examples for all endpoints

## Key Features

- **Scenario Management** - Start, stop, restart ROS2 launch scenarios
- **Model Checking** - Online safety verification with CTL model checker
- **Data Recording** - ROS bag recording with topic selection
- **ROS2 Integration** - Real-time topic subscription and publishing
- **Position Management** - Goal picker integration with coordinate conversion

## Web Interface

Access the ADORe Mission Control interface at `http://localhost:8888` for a complete web-based dashboard.

The Scenario Manager tab provides scenario selection, loop and model-check options, Start,
Restart and Halt All controls, and live scenario output. Scenario source is not editable from
the dashboard: edit launch files under the scenario directory directly.

## Base URL

```
http://localhost:8888/api
```
