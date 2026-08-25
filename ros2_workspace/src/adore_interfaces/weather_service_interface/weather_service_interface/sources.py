from __future__ import annotations

import time
import logging
from abc import ABC, abstractmethod
from typing import Optional

import requests

from .forecast import WeatherForecast, HourlyEntry

log = logging.getLogger(__name__)


class WeatherSource(ABC):
    name: str

    @abstractmethod
    def fetch(self, lat: float, lon: float, timeout_s: float) -> Optional[WeatherForecast]:
        ...


class NOAASource(WeatherSource):
    name = 'noaa'

    _POINTS_URL = 'https://api.weather.gov/points/{lat},{lon}'
    _HEADERS = {'User-Agent': 'weather_service_interface/1.0 (ros2-node)'}

    def fetch(self, lat: float, lon: float, timeout_s: float) -> Optional[WeatherForecast]:
        try:
            points_url = self._POINTS_URL.format(lat=round(lat, 4), lon=round(lon, 4))
            r = requests.get(points_url, headers=self._HEADERS, timeout=timeout_s)
            if r.status_code == 404:
                log.debug('NOAA: location outside coverage (%.4f, %.4f)', lat, lon)
                return None
            r.raise_for_status()
            props = r.json()['properties']
            forecast_hourly_url = props['forecastHourly']

            r2 = requests.get(forecast_hourly_url, headers=self._HEADERS, timeout=timeout_s)
            r2.raise_for_status()
            periods = r2.json()['properties']['periods']

            hourly: list[HourlyEntry] = []
            for p in periods[:48]:
                wind_spd_raw: str = p.get('windSpeed', '0 mph')
                try:
                    wind_kmh = float(wind_spd_raw.split()[0]) * 1.60934
                except (ValueError, IndexError):
                    wind_kmh = 0.0

                temp_c = (p['temperature'] - 32) * 5 / 9 if p.get('temperatureUnit') == 'F' else float(p['temperature'])

                hourly.append(HourlyEntry(
                    time_iso=p['startTime'],
                    temperature_c=round(temp_c, 1),
                    apparent_temperature_c=round(temp_c, 1),
                    precipitation_mm=0.0,
                    precipitation_probability_pct=float(p.get('probabilityOfPrecipitation', {}).get('value') or 0),
                    wind_speed_kmh=round(wind_kmh, 1),
                    wind_direction_deg=0.0,
                    wind_gusts_kmh=0.0,
                    cloud_cover_pct=0.0,
                    visibility_m=0.0,
                    weather_code=0,
                    weather_description=p.get('shortForecast', ''),
                ))

            now = time.time()
            return WeatherForecast(
                source='noaa',
                latitude=lat,
                longitude=lon,
                fetch_time_unix=now,
                valid_until_unix=now + 3600 * 48,
                timezone='UTC',
                hourly=hourly,
            )
        except requests.RequestException as e:
            log.warning('NOAA fetch failed: %s', e)
            return None
        except Exception as e:
            log.warning('NOAA parse error: %s', e)
            return None


class DWDSource(WeatherSource):
    """Deutscher Wetterdienst via Brightsky API.

    Default Brightsky units (no units param): temperature °C, wind km/h,
    precipitation mm, precipitation_probability 0-100 integer.
    """
    name = 'dwd'

    _URL = 'https://api.brightsky.dev/weather'

    def fetch(self, lat: float, lon: float, timeout_s: float) -> Optional[WeatherForecast]:
        try:
            from datetime import datetime, timezone, timedelta
            now_utc = datetime.now(timezone.utc)
            date_from = now_utc.strftime('%Y-%m-%dT%H:%M:%S')
            date_to   = (now_utc + timedelta(hours=48)).strftime('%Y-%m-%dT%H:%M:%S')

            params = {
                'lat': lat,
                'lon': lon,
                'date': date_from,
                'last_date': date_to,
            }
            r = requests.get(self._URL, params=params, timeout=timeout_s)
            r.raise_for_status()
            data = r.json()

            hourly: list[HourlyEntry] = []
            for entry in data.get('weather', []):
                condition = entry.get('condition', '')
                icon = entry.get('icon', '')
                hourly.append(HourlyEntry(
                    time_iso=entry.get('timestamp', ''),
                    temperature_c=float(entry.get('temperature') or 0),
                    apparent_temperature_c=float(entry.get('temperature') or 0),
                    precipitation_mm=float(entry.get('precipitation') or 0),
                    precipitation_probability_pct=float(entry.get('precipitation_probability') or 0),
                    wind_speed_kmh=float(entry.get('wind_speed') or 0),
                    wind_direction_deg=float(entry.get('wind_direction') or 0),
                    wind_gusts_kmh=float(entry.get('wind_gust_speed') or 0),
                    cloud_cover_pct=float(entry.get('cloud_cover') or 0),
                    visibility_m=float(entry.get('visibility') or 0),
                    weather_code=0,
                    weather_description=condition or icon,
                ))

            now_ts = time.time()
            return WeatherForecast(
                source='dwd',
                latitude=lat,
                longitude=lon,
                fetch_time_unix=now_ts,
                valid_until_unix=now_ts + 3600 * 48,
                timezone=data.get('sources', [{}])[0].get('timezone', 'UTC'),
                hourly=hourly,
            )
        except requests.RequestException as e:
            log.warning('DWD fetch failed: %s', e)
            return None
        except Exception as e:
            log.warning('DWD parse error: %s', e)
            return None


class OpenMeteoSource(WeatherSource):
    """Open-Meteo: free, no API key, global coverage. Used as fallback."""
    name = 'open_meteo'

    _URL = 'https://api.open-meteo.com/v1/forecast'

    _HOURLY_VARS = [
        'temperature_2m',
        'apparent_temperature',
        'precipitation',
        'precipitation_probability',
        'wind_speed_10m',
        'wind_direction_10m',
        'wind_gusts_10m',
        'cloud_cover',
        'visibility',
        'weather_code',
    ]

    def fetch(self, lat: float, lon: float, timeout_s: float) -> Optional[WeatherForecast]:
        try:
            params = {
                'latitude': lat,
                'longitude': lon,
                'hourly': ','.join(self._HOURLY_VARS),
                'forecast_days': 2,
                'wind_speed_unit': 'kmh',
                'timezone': 'UTC',
            }
            r = requests.get(self._URL, params=params, timeout=timeout_s)
            r.raise_for_status()
            data = r.json()

            h = data.get('hourly', {})
            times = h.get('time', [])
            n = len(times)

            def _col(key: str) -> list:
                vals = h.get(key, [None] * n)
                return [v if v is not None else 0 for v in vals]

            temps     = _col('temperature_2m')
            feels     = _col('apparent_temperature')
            precip    = _col('precipitation')
            precip_p  = _col('precipitation_probability')
            wspd      = _col('wind_speed_10m')
            wdir      = _col('wind_direction_10m')
            wgust     = _col('wind_gusts_10m')
            cloud     = _col('cloud_cover')
            vis       = _col('visibility')
            wcodes    = _col('weather_code')

            hourly: list[HourlyEntry] = []
            for i in range(n):
                code = int(wcodes[i])
                hourly.append(HourlyEntry(
                    time_iso=times[i],
                    temperature_c=float(temps[i]),
                    apparent_temperature_c=float(feels[i]),
                    precipitation_mm=float(precip[i]),
                    precipitation_probability_pct=float(precip_p[i]),
                    wind_speed_kmh=float(wspd[i]),
                    wind_direction_deg=float(wdir[i]),
                    wind_gusts_kmh=float(wgust[i]),
                    cloud_cover_pct=float(cloud[i]),
                    visibility_m=float(vis[i]),
                    weather_code=code,
                    weather_description=WeatherForecast.weather_code_description(code),
                ))

            now = time.time()
            return WeatherForecast(
                source='open_meteo',
                latitude=data.get('latitude', lat),
                longitude=data.get('longitude', lon),
                fetch_time_unix=now,
                valid_until_unix=now + 3600 * 48,
                timezone=data.get('timezone', 'UTC'),
                hourly=hourly,
            )
        except requests.RequestException as e:
            log.warning('Open-Meteo fetch failed: %s', e)
            return None
        except Exception as e:
            log.warning('Open-Meteo parse error: %s', e)
            return None


def build_source_chain(sources_cfg: dict) -> list[WeatherSource]:
    registry: dict[str, WeatherSource] = {
        'noaa':       NOAASource(),
        'dwd':        DWDSource(),
        'open_meteo': OpenMeteoSource(),
    }
    enabled = [
        (name, src)
        for name, src in registry.items()
        if sources_cfg.get(name, {}).get('enabled', True)
    ]
    enabled.sort(key=lambda x: sources_cfg.get(x[0], {}).get('priority', 99))
    return [src for _, src in enabled]
