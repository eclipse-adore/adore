from __future__ import annotations

import json
import os
import time
from pathlib import Path

from .forecast import WeatherForecast


class ForecastLogger:
    def __init__(self, enabled: bool, max_files: int = 100):
        self._enabled = enabled
        self._max_files = max_files
        self._log_dir = self._resolve_log_dir()
        if self._enabled:
            self._log_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _resolve_log_dir() -> Path:
        ros_home = os.environ.get('ROS_HOME', os.path.expanduser('~/.ros'))
        return Path(ros_home) / 'weather_forecasts'

    def log(self, forecast: WeatherForecast) -> None:
        if not self._enabled:
            return

        ts = int(forecast.fetch_time_unix)
        filename = self._log_dir / f'forecast_{ts}_{forecast.source}.json'
        with open(filename, 'w') as f:
            json.dump(forecast.to_dict(), f, indent=2)

        self._prune()

    def _prune(self) -> None:
        files = sorted(self._log_dir.glob('forecast_*.json'), key=lambda p: p.stat().st_mtime)
        excess = len(files) - self._max_files
        for f in files[:excess]:
            f.unlink(missing_ok=True)
