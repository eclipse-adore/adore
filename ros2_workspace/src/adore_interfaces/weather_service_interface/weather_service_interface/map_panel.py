from __future__ import annotations

import io
import math
import threading
import time
from typing import Optional

import requests
from PIL import Image

# ── OSM tile helpers ──────────────────────────────────────────────────────────

_TILE_URL = 'https://tile.openstreetmap.org/{z}/{x}/{y}.png'
_TILE_SIZE = 256
_HEADERS = {'User-Agent': 'weather_service_interface/1.0 (ros2-node; map-panel)'}

_tile_cache: dict[tuple[int, int, int], Optional[Image.Image]] = {}
_tile_lock  = threading.Lock()


def _deg_to_tile(lat: float, lon: float, zoom: int) -> tuple[int, int]:
    n = 1 << zoom
    x = int((lon + 180.0) / 360.0 * n)
    lat_r = math.radians(lat)
    y = int((1.0 - math.log(math.tan(lat_r) + 1.0 / math.cos(lat_r)) / math.pi) / 2.0 * n)
    return x, y


def _tile_origin_deg(tx: int, ty: int, zoom: int) -> tuple[float, float]:
    """Return (lat, lon) of the NW corner of tile (tx, ty)."""
    n = 1 << zoom
    lon = tx / n * 360.0 - 180.0
    lat = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * ty / n))))
    return lat, lon


def _fetch_tile(z: int, x: int, y: int) -> Optional[Image.Image]:
    key = (z, x, y)
    with _tile_lock:
        if key in _tile_cache:
            return _tile_cache[key]

    try:
        r = requests.get(
            _TILE_URL.format(z=z, x=x, y=y),
            headers=_HEADERS,
            timeout=5.0,
        )
        r.raise_for_status()
        img = Image.open(io.BytesIO(r.content)).convert('L')
    except Exception:
        img = None

    with _tile_lock:
        _tile_cache[key] = img

    return img


# ── braille rendering ─────────────────────────────────────────────────────────

# Braille block is 2 cols × 4 rows of dots.
# Unicode U+2800 is the empty braille cell; each dot adds a fixed offset.
#   dot layout (col, row) -> bit
#     (0,0)->0  (1,0)->3
#     (0,1)->1  (1,1)->4
#     (0,2)->2  (1,2)->5
#     (0,3)->6  (1,3)->7
_DOT_BIT = [
    [0, 3],
    [1, 4],
    [2, 5],
    [6, 7],
]

_THRESHOLD = 180


def _pixels_to_braille(pixels: list[list[int]]) -> str:
    """Convert a 2-wide × 4-tall pixel block to a braille character."""
    bits = 0
    for row in range(4):
        for col in range(2):
            if pixels[row][col] < _THRESHOLD:
                bits |= (1 << _DOT_BIT[row][col])
    return chr(0x2800 + bits)


def _image_to_braille(img: Image.Image, cols: int, rows: int) -> list[str]:
    """Resize img to (cols*2) × (rows*4) and render as braille lines."""
    img = img.resize((cols * 2, rows * 4), Image.LANCZOS)
    px = list(img.getdata())
    w = cols * 2

    lines: list[str] = []
    for br in range(rows):
        line = ''
        for bc in range(cols):
            block = [
                [px[(br * 4 + dr) * w + bc * 2 + dc] for dc in range(2)]
                for dr in range(4)
            ]
            line += _pixels_to_braille(block)
        lines.append(line)
    return lines


# ── MapPanel ──────────────────────────────────────────────────────────────────

class MapPanel:
    """Async OSM tile fetcher and braille renderer.

    Call render() from the curses loop; it returns immediately with whatever
    is cached. Tile fetches happen on background threads.
    """

    _ZOOM = 13
    # How many tiles to stitch in each direction around the centre tile.
    _RADIUS = 1  # 3x3 grid

    def __init__(self) -> None:
        self._lat: Optional[float] = None
        self._lon: Optional[float] = None
        self._lock = threading.Lock()

        # Last rendered state -- reuse if position hasn't changed much
        self._last_render_lat: Optional[float] = None
        self._last_render_lon: Optional[float] = None
        self._last_render_size: tuple[int, int] = (0, 0)
        self._cached_lines: list[str] = []
        self._cached_ts: float = 0.0

        self._pending_fetches: set[tuple[int, int, int]] = set()
        self._fetch_lock = threading.Lock()

    def update_position(self, lat: float, lon: float) -> None:
        with self._lock:
            self._lat = lat
            self._lon = lon

    def _tiles_for_position(self, lat: float, lon: float) -> list[tuple[int, int, int]]:
        cx, cy = _deg_to_tile(lat, lon, self._ZOOM)
        r = self._RADIUS
        return [
            (self._ZOOM, cx + dx, cy + dy)
            for dy in range(-r, r + 1)
            for dx in range(-r, r + 1)
        ]

    def _ensure_tiles_fetched(self, tiles: list[tuple[int, int, int]]) -> None:
        to_fetch = []
        with _tile_lock:
            for key in tiles:
                if key not in _tile_cache:
                    to_fetch.append(key)

        with self._fetch_lock:
            for key in to_fetch:
                if key not in self._pending_fetches:
                    self._pending_fetches.add(key)
                    z, x, y = key
                    t = threading.Thread(
                        target=self._fetch_and_clear,
                        args=(z, x, y),
                        daemon=True,
                    )
                    t.start()

    def _fetch_and_clear(self, z: int, x: int, y: int) -> None:
        _fetch_tile(z, x, y)
        with self._fetch_lock:
            self._pending_fetches.discard((z, x, y))

    def _stitch_tiles(
        self,
        lat: float,
        lon: float,
        px_w: int,
        px_h: int,
    ) -> Image.Image:
        cx, cy = _deg_to_tile(lat, lon, self._ZOOM)
        r = self._RADIUS
        grid_dim = 2 * r + 1
        canvas = Image.new('L', (grid_dim * _TILE_SIZE, grid_dim * _TILE_SIZE), color=200)

        for dy in range(-r, r + 1):
            for dx in range(-r, r + 1):
                tile = _fetch_tile(self._ZOOM, cx + dx, cy + dy)
                if tile is not None:
                    canvas.paste(tile, ((dx + r) * _TILE_SIZE, (dy + r) * _TILE_SIZE))

        # Pixel offset of (lat, lon) within the stitched canvas
        tile_lat, tile_lon = _tile_origin_deg(cx - r, cy - r, self._ZOOM)
        _, tile_lon_end = _tile_origin_deg(cx + r + 1, cy - r, self._ZOOM)
        tile_lat_bot, _ = _tile_origin_deg(cx - r, cy + r + 1, self._ZOOM)

        lon_span = tile_lon_end - tile_lon
        lat_span = tile_lat - tile_lat_bot

        if lon_span <= 0 or lat_span <= 0:
            return canvas.crop((0, 0, px_w, px_h))

        cx_px = int((lon - tile_lon) / lon_span * canvas.width)
        cy_px = int((tile_lat - lat) / lat_span * canvas.height)

        # Crop centred on the vehicle position
        left   = max(0, cx_px - px_w // 2)
        top    = max(0, cy_px - px_h // 2)
        right  = left + px_w
        bottom = top  + px_h

        if right > canvas.width:
            right = canvas.width
            left  = max(0, right - px_w)
        if bottom > canvas.height:
            bottom = canvas.height
            top    = max(0, bottom - px_h)

        return canvas.crop((left, top, right, bottom)), (cx_px - left, cy_px - top)

    def render(self, cols: int, rows: int) -> tuple[list[str], tuple[int, int] | None]:
        """Return (braille_lines, marker_cell) where marker_cell is (col, row)
        of the vehicle position in braille-cell coordinates, or None."""
        with self._lock:
            lat = self._lat
            lon = self._lon

        if lat is None or lon is None:
            waiting = ['No position fix'] + [''] * (rows - 1)
            return waiting, None

        tiles = self._tiles_for_position(lat, lon)
        self._ensure_tiles_fetched(tiles)

        # Check cache validity: re-render if position moved >10m or size changed
        if (
            self._last_render_size == (cols, rows)
            and self._last_render_lat is not None
            and abs(lat - self._last_render_lat) < 0.0001
            and abs(lon - self._last_render_lon) < 0.0001
            and self._cached_lines
            and (time.monotonic() - self._cached_ts) < 10.0
        ):
            with _tile_lock:
                all_loaded = all(k in _tile_cache and _tile_cache[k] is not None for k in tiles)
            if all_loaded:
                return self._cached_lines, self._marker_cell

        px_w = cols * 2
        px_h = rows * 4

        try:
            result = self._stitch_tiles(lat, lon, px_w, px_h)
            if isinstance(result, tuple):
                canvas, (veh_px_x, veh_px_y) = result
            else:
                canvas = result
                veh_px_x = px_w // 2
                veh_px_y = px_h // 2
        except Exception:
            lines = ['Map error'] + [''] * (rows - 1)
            return lines, None

        lines = _image_to_braille(canvas, cols, rows)

        # Braille-cell coordinates of the vehicle
        marker_col = min(veh_px_x // 2, cols - 1)
        marker_row = min(veh_px_y // 4, rows - 1)

        self._cached_lines = lines
        self._marker_cell = (marker_col, marker_row)
        self._last_render_lat = lat
        self._last_render_lon = lon
        self._last_render_size = (cols, rows)
        self._cached_ts = time.monotonic()

        return lines, (marker_col, marker_row)
