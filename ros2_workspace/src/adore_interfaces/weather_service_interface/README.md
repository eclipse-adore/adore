# weather_service_interface

ROS 2 weather forecast service for autonomous vehicles. Fetches forecasts from external weather APIs based on ego vehicle position and publishes them at low frequency.

## Nodes

### `weather_service_node`

Subscribes to the ego vehicle GPS position and fetches weather data when the vehicle moves beyond a configurable displacement threshold or the cached forecast expires. Publishes forecast JSON to `/ego_vehicle/weather_forecast` at a configurable low frequency (default 0.1 Hz).

**Subscribed topics**
- `/ego_vehicle/vehicle_state_dynamic_nav_sat_fix` (`sensor_msgs/NavSatFix`)

**Published topics**
- `/ego_vehicle/weather_forecast` (`std_msgs/String` — JSON-serialized forecast)

**Forecast logs** are written to `$ROS_HOME/weather_forecasts/` on each successful fetch.

### `weather_visualizer_node` _(optional)_

Terminal-based curses dashboard showing the next 12 hours of forecast data. Must be run in a separate terminal with a real TTY — it cannot be a child of `ros2 launch`.

## Data sources

Sources are tried in priority order. Set `enabled: false` in config to skip one.

| Priority | Source | Coverage | API key |
|----------|--------|----------|---------|
| 1 | DWD via Brightsky (`api.brightsky.dev`) | Germany / Europe | None |
| 2 | NOAA (`api.weather.gov`) | US only | None |
| 3 | Open-Meteo (`api.open-meteo.com`) | Global (fallback) | None |

## Configuration

`config/weather_service_config.yaml`

```yaml
fetch:
  displacement_threshold_m: 5000.0   # minimum vehicle movement before re-fetch
  max_forecast_age_s: 3600.0         # force re-fetch after this age
  check_interval_s: 60.0             # how often to check if fetch is needed
  publish_interval_s: 10.0           # forecast publish rate (0.1 Hz default)

sources:
  noaa:       { enabled: true,  priority: 1 }
  dwd:        { enabled: true,  priority: 2 }
  open_meteo: { enabled: true,  priority: 3 }

logging:
  enabled: true
  max_files: 100
```

## Usage

### Without Docker

```bash
# build
colcon build --packages-select weather_service_interface

# service only
./start_weather_service.sh

# service + visualizer (separate terminals)
./start_weather_service.sh
./start_visualizer.sh
```

### With Docker

```bash
make build

make run                # service only
make run_visualizer     # service in background + visualizer with TTY
make shell              # interactive shell in container
```

Override config or ROS domain on the command line:

```bash
make run CONFIG=/path/to/custom_config.yaml ROS_DOMAIN_ID=42
```

Service logs are written to `/tmp/weather_service.log` when running via `run_visualizer`. Forecast JSON files land in `$ROS_HOME/weather_forecasts/` on the host via the bind mount.

## Visualizer keys

| Key | Action |
|-----|--------|
| `q` / `ESC` | Quit |
