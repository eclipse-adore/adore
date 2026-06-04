from __future__ import annotations

import curses
import json
import signal
import threading
import time
from datetime import datetime, timezone, timedelta
from typing import Optional

import rclpy
from rclpy.node import Node
from rclpy.executors import MultiThreadedExecutor
from std_msgs.msg import String

from .forecast import WeatherForecast, HourlyEntry


def _wind_compass(deg: float) -> str:
    dirs = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW']
    return dirs[int((deg + 22.5) / 45.0) % 8]


def _wind_arrow(deg: float) -> str:
    arrows = ['↑', '↗', '→', '↘', '↓', '↙', '←', '↖']
    return arrows[int((deg + 22.5) / 45.0) % 8]


_SPARKS = ' ▁▂▃▄▅▆▇█'


def _sparkline(values: list[float], width: int) -> str:
    if not values:
        return ' ' * width
    samples = values[:width]
    lo, hi = min(samples), max(samples)
    span = hi - lo or 1
    return ''.join(_SPARKS[min(int((v - lo) / span * 8), 8)] for v in samples)


def _upcoming_hours(hourly: list[HourlyEntry], hours: int = 12) -> list[HourlyEntry]:
    """Return entries from the next upcoming hour onward, up to `hours` entries."""
    now_utc = datetime.now(timezone.utc)
    result: list[HourlyEntry] = []
    for entry in hourly:
        try:
            ts = entry.time_iso
            # Brightsky returns RFC3339 with offset; Open-Meteo returns naive UTC
            if ts.endswith('Z'):
                ts = ts[:-1] + '+00:00'
            dt = datetime.fromisoformat(ts)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            if dt >= now_utc - timedelta(minutes=30):
                result.append(entry)
                if len(result) >= hours:
                    break
        except ValueError:
            continue
    return result


class WeatherVisualizerNode(Node):
    def __init__(self):
        super().__init__('weather_visualizer_node')
        self.declare_parameter('topic', '/ego_vehicle/weather_forecast')
        self.declare_parameter('queue_depth', 10)

        topic       = self.get_parameter('topic').get_parameter_value().string_value
        queue_depth = self.get_parameter('queue_depth').get_parameter_value().integer_value

        self._forecast: Optional[WeatherForecast] = None
        self._lock     = threading.Lock()
        self._shutdown = threading.Event()
        self._last_msg_t: Optional[float] = None

        self._sub = self.create_subscription(
            String,
            topic,
            self._forecast_callback,
            queue_depth,
        )
        self.get_logger().info(f'WeatherVisualizerNode watching {topic}')

    def _forecast_callback(self, msg: String) -> None:
        try:
            data = json.loads(msg.data)
            hourly = [HourlyEntry(**e) for e in data.pop('hourly', [])]
            forecast = WeatherForecast(**data, hourly=hourly)
            with self._lock:
                self._forecast = forecast
                self._last_msg_t = time.monotonic()
        except Exception as e:
            self.get_logger().warning(f'Failed to parse forecast message: {e}')

    def get_state(self) -> tuple[Optional[WeatherForecast], Optional[float]]:
        with self._lock:
            return self._forecast, self._last_msg_t

    def is_shutdown(self) -> bool:
        return self._shutdown.is_set()

    def shutdown(self) -> None:
        self._shutdown.set()


# ── curses rendering (runs on main thread) ────────────────────────────────────

def _safe_addstr(win, y: int, x: int, text: str, attr: int = 0) -> None:
    try:
        win.addstr(y, x, text, attr)
    except curses.error:
        pass


def _draw_header(stdscr, width: int, forecast: Optional[WeatherForecast], stale: bool) -> None:
    title = ' WEATHER FORECAST DASHBOARD '
    pad = max(0, (width - len(title)) // 2)
    _safe_addstr(stdscr, 0, pad, title, curses.color_pair(1) | curses.A_BOLD | curses.A_REVERSE)

    if forecast:
        age_s = int(time.time() - forecast.fetch_time_unix)
        age_str = f'{age_s // 60}m{age_s % 60:02d}s ago'
        src_line = (
            f'Source: {forecast.source.upper()}  |  '
            f'({forecast.latitude:.4f}, {forecast.longitude:.4f})  |  '
            f'Fetched: {age_str}'
        )
    else:
        src_line = 'Waiting for forecast data...'

    dot       = '●' if not stale else '○'
    dot_color = curses.color_pair(4) if not stale else curses.color_pair(5)
    _safe_addstr(stdscr, 1, 1, dot, dot_color)
    _safe_addstr(stdscr, 1, 3, src_line[:width - 4], curses.color_pair(7))


def _draw_waiting(stdscr, height: int, width: int) -> None:
    msg = '[ Waiting for /ego_vehicle/weather_forecast ]'
    _safe_addstr(stdscr, height // 2, max(0, (width - len(msg)) // 2),
                 msg, curses.color_pair(3) | curses.A_BOLD)


def _draw_current(stdscr, entry: HourlyEntry, width: int) -> None:
    temp_color = curses.color_pair(2) if entry.temperature_c > 20 else (
        curses.color_pair(3) if entry.temperature_c < 5 else curses.color_pair(6)
    )
    time_label = entry.time_iso[11:16] if len(entry.time_iso) >= 16 else ''
    _safe_addstr(stdscr, 3, 2, f'NEXT HOUR  {time_label}', curses.color_pair(1) | curses.A_BOLD)
    _safe_addstr(stdscr, 3, 22,
        f'{entry.temperature_c:+.1f}°C  feels {entry.apparent_temperature_c:+.1f}°C',
        temp_color | curses.A_BOLD,
    )
    _safe_addstr(stdscr, 4, 2,
        f'Wind: {_wind_arrow(entry.wind_direction_deg)} {_wind_compass(entry.wind_direction_deg)} '
        f'{entry.wind_speed_kmh:.0f} km/h  gusts {entry.wind_gusts_kmh:.0f} km/h',
        curses.color_pair(6),
    )
    precip_color = curses.color_pair(3) if entry.precipitation_mm > 0.5 else curses.color_pair(6)
    _safe_addstr(stdscr, 5, 2,
        f'Precip: {entry.precipitation_mm:.1f} mm  ({entry.precipitation_probability_pct:.0f}% chance)',
        precip_color,
    )
    _safe_addstr(stdscr, 6, 2,
        f'Cloud: {entry.cloud_cover_pct:.0f}%  Visibility: {entry.visibility_m / 1000:.1f} km',
        curses.color_pair(6),
    )
    _safe_addstr(stdscr, 7, 2,
        f'Conditions: {entry.weather_description[:width - 16]}',
        curses.color_pair(6) | curses.A_ITALIC,
    )


def _draw_hourly_table(stdscr, entries: list[HourlyEntry], height: int, width: int) -> int:
    row = 9
    if row >= height - 4:
        return row

    header = (
        f"{'Time':>5}  {'°C':>5}  {'Fl':>5}  {'Prcp':>5}  "
        f"{'Prob':>4}  {'Wspd':>5}  {'Gust':>5}  {'Dir':>3}  {'Cld':>3}  Conditions"
    )
    _safe_addstr(stdscr, row, 2, header[:width - 3], curses.color_pair(1) | curses.A_UNDERLINE)
    row += 1

    for entry in entries:
        if row >= height - 4:
            break
        time_part = entry.time_iso[11:16] if len(entry.time_iso) >= 16 else entry.time_iso[:5]
        temp_color = curses.color_pair(2) if entry.temperature_c > 20 else (
            curses.color_pair(3) if entry.temperature_c < 5 else curses.color_pair(6)
        )
        line = (
            f"{time_part:>5}  "
            f"{entry.temperature_c:>+5.1f}  "
            f"{entry.apparent_temperature_c:>+5.1f}  "
            f"{entry.precipitation_mm:>5.1f}  "
            f"{entry.precipitation_probability_pct:>3.0f}%  "
            f"{entry.wind_speed_kmh:>5.0f}  "
            f"{entry.wind_gusts_kmh:>5.0f}  "
            f"{_wind_compass(entry.wind_direction_deg):>3}  "
            f"{entry.cloud_cover_pct:>3.0f}%  "
            f"{entry.weather_description[:20]}"
        )
        _safe_addstr(stdscr, row, 2, line[:width - 3], temp_color)
        row += 1

    return row


def _draw_sparklines(stdscr, entries: list[HourlyEntry], height: int, width: int) -> None:
    spark_row = height - 4
    if spark_row < 10:
        return
    spark_width = min(len(entries), width - 20)
    temps  = [h.temperature_c for h in entries]
    precip = [h.precipitation_mm for h in entries]
    _safe_addstr(stdscr, spark_row,     2, 'Temp  12h: ', curses.color_pair(2))
    _safe_addstr(stdscr, spark_row,     13, _sparkline(temps, spark_width), curses.color_pair(2) | curses.A_BOLD)
    _safe_addstr(stdscr, spark_row + 1, 2, 'Precip 12h:', curses.color_pair(3))
    _safe_addstr(stdscr, spark_row + 1, 13, _sparkline(precip, spark_width), curses.color_pair(3) | curses.A_BOLD)


def _draw_footer(stdscr, height: int, width: int) -> None:
    footer = ' [q] Quit '
    _safe_addstr(stdscr, height - 1, 0, footer.ljust(width - 1)[:width - 1], curses.A_REVERSE)


def _curses_loop(stdscr, node: WeatherVisualizerNode) -> None:
    curses.curs_set(0)
    stdscr.nodelay(True)
    stdscr.timeout(500)

    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(1, curses.COLOR_CYAN,    -1)
    curses.init_pair(2, curses.COLOR_YELLOW,  -1)
    curses.init_pair(3, curses.COLOR_BLUE,    -1)
    curses.init_pair(4, curses.COLOR_GREEN,   -1)
    curses.init_pair(5, curses.COLOR_RED,     -1)
    curses.init_pair(6, curses.COLOR_WHITE,   -1)
    curses.init_pair(7, curses.COLOR_MAGENTA, -1)

    while not node.is_shutdown():
        key = stdscr.getch()
        if key in (ord('q'), ord('Q'), 27):
            node.shutdown()
            break

        forecast, last_t = node.get_state()
        stale = (last_t is None) or ((time.monotonic() - last_t) > 120)

        height, width = stdscr.getmaxyx()
        stdscr.erase()

        _draw_header(stdscr, width, forecast, stale)

        if forecast is None or not forecast.hourly:
            _draw_waiting(stdscr, height, width)
        else:
            upcoming = _upcoming_hours(forecast.hourly, hours=12)
            if not upcoming:
                _draw_waiting(stdscr, height, width)
            else:
                _draw_current(stdscr, upcoming[0], width)
                _draw_hourly_table(stdscr, upcoming, height, width)
                _draw_sparklines(stdscr, upcoming, height, width)

        _draw_footer(stdscr, height, width)
        try:
            stdscr.refresh()
        except curses.error:
            pass


def main(args=None):
    rclpy.init(args=args)
    try:
        node = WeatherVisualizerNode()
    except Exception:
        rclpy.shutdown()
        return

    executor = MultiThreadedExecutor()
    executor.add_node(node)

    # Spin the executor on a background thread so the main thread can own the TTY for curses
    spin_thread = threading.Thread(
        target=lambda: _spin_until_shutdown(executor, node),
        daemon=True,
    )

    shutdown_event = threading.Event()

    def _signal_handler(sig, frame):
        shutdown_event.set()
        node.shutdown()

    signal.signal(signal.SIGINT,  _signal_handler)
    signal.signal(signal.SIGTERM, _signal_handler)

    spin_thread.start()

    try:
        curses.wrapper(_curses_loop, node)
    except Exception as e:
        node.get_logger().error(f'Curses error: {e}')
    finally:
        node.shutdown()
        shutdown_event.set()
        spin_thread.join(timeout=2.0)
        executor.shutdown()
        node.destroy_node()
        rclpy.shutdown()


def _spin_until_shutdown(executor: MultiThreadedExecutor, node: WeatherVisualizerNode) -> None:
    while not node.is_shutdown():
        executor.spin_once(timeout_sec=0.1)
