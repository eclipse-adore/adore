from __future__ import annotations

import time
from dataclasses import dataclass, field, asdict
from typing import Optional


@dataclass
class HourlyEntry:
    time_iso: str
    temperature_c: float
    apparent_temperature_c: float
    precipitation_mm: float
    precipitation_probability_pct: float
    wind_speed_kmh: float
    wind_direction_deg: float
    wind_gusts_kmh: float
    cloud_cover_pct: float
    visibility_m: float
    weather_code: int
    weather_description: str


@dataclass
class WeatherForecast:
    source: str
    latitude: float
    longitude: float
    fetch_time_unix: float
    valid_until_unix: float
    timezone: str
    hourly: list[HourlyEntry] = field(default_factory=list)

    def is_expired(self, max_age_s: float) -> bool:
        return (time.time() - self.fetch_time_unix) > max_age_s

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def weather_code_description(code: int) -> str:
        _WMO = {
            0:  'Clear sky',
            1:  'Mainly clear', 2: 'Partly cloudy', 3: 'Overcast',
            45: 'Fog', 48: 'Depositing rime fog',
            51: 'Light drizzle', 53: 'Moderate drizzle', 55: 'Dense drizzle',
            61: 'Slight rain', 63: 'Moderate rain', 65: 'Heavy rain',
            71: 'Slight snow', 73: 'Moderate snow', 75: 'Heavy snow',
            77: 'Snow grains',
            80: 'Slight showers', 81: 'Moderate showers', 82: 'Violent showers',
            85: 'Slight snow showers', 86: 'Heavy snow showers',
            95: 'Thunderstorm', 96: 'Thunderstorm with slight hail',
            99: 'Thunderstorm with heavy hail',
        }
        return _WMO.get(code, f'Unknown ({code})')
