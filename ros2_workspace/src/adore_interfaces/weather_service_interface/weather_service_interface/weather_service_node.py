from __future__ import annotations

import json
import math
import os
import signal
import threading
import time
import yaml
from typing import Optional

import rclpy
from rclpy.node import Node
from rclpy.executors import MultiThreadedExecutor
from sensor_msgs.msg import NavSatFix
from std_msgs.msg import String
from ament_index_python.packages import get_package_share_directory

from .forecast import WeatherForecast
from .forecast_logger import ForecastLogger
from .sources import build_source_chain


def _haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6_371_000.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


class WeatherServiceNode(Node):
    def __init__(self):
        super().__init__('weather_service_node')
        self.declare_parameter('config_path', '')

        config_path = self.get_parameter('config_path').get_parameter_value().string_value
        if not config_path:
            config_path = os.path.join(
                get_package_share_directory('weather_service_interface'),
                'config', 'weather_service_config.yaml',
            )

        if not os.path.exists(config_path):
            self.get_logger().error(f'Config not found: {config_path}')
            raise RuntimeError(f'Config not found: {config_path}')

        with open(config_path, 'r') as f:
            self._cfg = yaml.safe_load(f)

        fetch_cfg   = self._cfg.get('fetch', {})
        log_cfg     = self._cfg.get('logging', {})
        topics_cfg  = self._cfg.get('topics', {})
        sources_cfg = self._cfg.get('sources', {})

        self._displacement_threshold_m: float = fetch_cfg.get('displacement_threshold_m', 5000.0)
        self._max_forecast_age_s: float       = fetch_cfg.get('max_forecast_age_s', 3600.0)
        self._check_interval_s: float         = fetch_cfg.get('check_interval_s', 60.0)
        self._publish_interval_s: float       = fetch_cfg.get('publish_interval_s', 10.0)

        self._source_chain   = build_source_chain(sources_cfg)
        self._sources_cfg    = sources_cfg
        self._forecast_logger = ForecastLogger(
            enabled=log_cfg.get('enabled', True),
            max_files=int(log_cfg.get('max_files', 100)),
        )

        nav_sat_topic     = topics_cfg.get('nav_sat_fix', '/ego_vehicle/vehicle_state_dynamic_nav_sat_fix')
        forecast_topic    = topics_cfg.get('weather_forecast', '/ego_vehicle/weather_forecast')
        queue_depth       = int(topics_cfg.get('queue_depth', 10))

        self._current_forecast: Optional[WeatherForecast] = None
        self._last_fetch_lat: Optional[float] = None
        self._last_fetch_lon: Optional[float] = None
        self._latest_lat: Optional[float] = None
        self._latest_lon: Optional[float] = None
        self._forecast_lock = threading.Lock()
        self._position_lock = threading.Lock()
        self._shutdown = threading.Event()

        self._sub = self.create_subscription(
            NavSatFix,
            nav_sat_topic,
            self._nav_sat_callback,
            queue_depth,
        )
        self._pub = self.create_publisher(String, forecast_topic, queue_depth)

        self._fetch_timer   = self.create_timer(self._check_interval_s,   self._check_and_fetch)
        self._publish_timer = self.create_timer(self._publish_interval_s, self._publish_forecast)

        if not self._source_chain:
            self.get_logger().error('No weather sources enabled. Check config.')
        else:
            names = ', '.join(s.name for s in self._source_chain)
            self.get_logger().info(f'Source priority chain: {names}')

        self.get_logger().info(
            f'WeatherServiceNode ready | '
            f'displacement threshold: {self._displacement_threshold_m:.0f} m | '
            f'max forecast age: {self._max_forecast_age_s:.0f} s | '
            f'publish interval: {self._publish_interval_s:.1f} s'
        )

    # ── position subscription ─────────────────────────────────────────────────

    def _nav_sat_callback(self, msg: NavSatFix) -> None:
        with self._position_lock:
            self._latest_lat = msg.latitude
            self._latest_lon = msg.longitude

    # ── fetch logic ───────────────────────────────────────────────────────────

    def _needs_fetch(self, lat: float, lon: float) -> bool:
        with self._forecast_lock:
            if self._current_forecast is None:
                return True

            if self._current_forecast.is_expired(self._max_forecast_age_s):
                self.get_logger().info('Forecast expired, triggering fetch.')
                return True

            if self._last_fetch_lat is None or self._last_fetch_lon is None:
                return True

            dist = _haversine_m(self._last_fetch_lat, self._last_fetch_lon, lat, lon)
            if dist >= self._displacement_threshold_m:
                self.get_logger().info(
                    f'Vehicle displaced {dist:.0f} m (threshold: {self._displacement_threshold_m:.0f} m), '
                    f'triggering fetch.'
                )
                return True

        return False

    def _do_fetch(self, lat: float, lon: float) -> None:
        for source in self._source_chain:
            timeout = self._sources_cfg.get(source.name, {}).get('timeout_s', 10.0)
            self.get_logger().info(f'Attempting fetch from {source.name} ({lat:.5f}, {lon:.5f})')
            try:
                forecast = source.fetch(lat, lon, timeout)
            except Exception as e:
                self.get_logger().warning(f'{source.name} raised exception: {e}')
                forecast = None

            if forecast is not None and forecast.hourly:
                with self._forecast_lock:
                    self._current_forecast = forecast
                    self._last_fetch_lat   = lat
                    self._last_fetch_lon   = lon
                self._forecast_logger.log(forecast)
                self.get_logger().info(
                    f'Forecast updated from {source.name}: '
                    f'{len(forecast.hourly)} hourly entries.'
                )
                return

            self.get_logger().warning(f'{source.name} returned no usable data, trying next source.')

        self.get_logger().error('All weather sources failed. Retaining previous forecast if available.')

    def _check_and_fetch(self) -> None:
        with self._position_lock:
            lat = self._latest_lat
            lon = self._latest_lon

        if lat is None or lon is None:
            self.get_logger().debug('No vehicle position yet, skipping fetch check.')
            return

        if self._needs_fetch(lat, lon):
            fetch_thread = threading.Thread(
                target=self._do_fetch, args=(lat, lon), daemon=True
            )
            fetch_thread.start()

    # ── publish ───────────────────────────────────────────────────────────────

    def _publish_forecast(self) -> None:
        with self._forecast_lock:
            forecast = self._current_forecast

        if forecast is None:
            return

        msg = String()
        msg.data = json.dumps(forecast.to_dict())
        self._pub.publish(msg)

    def shutdown(self) -> None:
        self._shutdown.set()


def main(args=None):
    rclpy.init(args=args)
    try:
        node = WeatherServiceNode()
    except RuntimeError:
        rclpy.shutdown()
        return

    executor = MultiThreadedExecutor()
    executor.add_node(node)

    shutdown_event = threading.Event()

    def _signal_handler(sig, frame):
        shutdown_event.set()

    signal.signal(signal.SIGINT,  _signal_handler)
    signal.signal(signal.SIGTERM, _signal_handler)

    try:
        while not shutdown_event.is_set():
            executor.spin_once(timeout_sec=0.1)
    finally:
        node.shutdown()
        executor.shutdown()
        node.destroy_node()
        rclpy.shutdown()
