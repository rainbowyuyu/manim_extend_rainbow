# rainbow_yu — import CS2 radar PNG into editable map bundle

from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image

from yty_manim.tools.map_editor.map_bundle import (
    DEFAULT_BG_RGB,
    DEFAULT_GRID_H,
    DEFAULT_GRID_W,
    DEFAULT_OBSTACLE_RGB,
    ExplosionSource,
    MapBundle,
    MapMarker,
)

_MIRAGE_RADAR = (
    Path(__file__).resolve().parents[3]
    / "video_project"
    / "cs2_c4"
    / "assets"
    / "de_mirage_radar.png"
)


def load_rgb(path: Path) -> np.ndarray:
    return np.array(Image.open(path).convert("RGB"))


def build_orange_exterior_mask(rgb: np.ndarray) -> np.ndarray:
    """Orange outlines / UI chrome outside playable map — exclude from walkable."""
    r, g, b = rgb[..., 0].astype(np.int16), rgb[..., 1].astype(np.int16), rgb[..., 2].astype(np.int16)
    orange = (
        (r > 150)
        & (g > 35)
        & (g < 165)
        & (b < 110)
        & (r > g + 12)
        & (g >= b - 15)
    )
    yellow_letter = (r > 175) & (g > 130) & (b < 120)
    return orange | yellow_letter


def build_walkability(rgb: np.ndarray, *, cs2_mirage: bool = True) -> np.ndarray:
    """Gray floor = walkable; dark brown = wall. CS2 colored zones forced walkable."""
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    lum = 0.299 * r + 0.587 * g + 0.114 * b
    walk = lum > 28
    red_site = (r > 100) & (g < 110) & (b < 110) & (r > g + 25)
    blue_spawn = (b > 90) & (r < 130) & (g < 150) & (b > r)
    yellow_spawn = (r > 140) & (g > 110) & (b < 110)
    green_zone = (g > 120) & (r < 120) & (b < 120) & (g > r + 20)
    walk = walk | red_site | blue_spawn | yellow_spawn | green_zone
    walk &= ~build_orange_exterior_mask(rgb)
    if cs2_mirage:
        h, w = walk.shape
        walk[int(h * 0.88) :, int(w * 0.72) :] = False
    return walk


def build_crate_mask(rgb: np.ndarray, walk: np.ndarray) -> np.ndarray:
    """Detect light-gray crate/box pixels on walkable floor."""
    r, g, b = rgb[..., 0].astype(np.int16), rgb[..., 1].astype(np.int16), rgb[..., 2].astype(np.int16)
    lum = 0.299 * r + 0.587 * g + 0.114 * b
    neutral = (np.abs(r - g) < 22) & (np.abs(g - b) < 22)
    light = (lum > 125) & (lum < 215)
    not_letter = ~((r > 150) & (g > 90) & (b < 130))
    not_orange = ~((r > 175) & (g > 55) & (g < 150) & (b < 90))
    not_green = ~((g > 130) & (r < 110) & (b < 110))
    return walk & neutral & light & not_letter & not_orange & not_green


def downsample_mask(mask: np.ndarray, gw: int, gh: int, threshold: float = 0.22) -> np.ndarray:
    h, w = mask.shape
    ys = np.linspace(0, h - 1, gh).astype(int)
    xs = np.linspace(0, w - 1, gw).astype(int)
    out = np.zeros((gh, gw), dtype=bool)
    for j, y in enumerate(ys):
        for i, x in enumerate(xs):
            y0, y1 = max(0, y - 2), min(h, y + 3)
            x0, x1 = max(0, x - 2), min(w, x + 3)
            out[j, i] = mask[y0:y1, x0:x1].mean() > threshold
    return out


def apply_crate_obstacles(
    rgb: np.ndarray,
    walk: np.ndarray,
    colors: np.ndarray,
    crate_grid: np.ndarray,
) -> None:
    h, w = rgb.shape[:2]
    gh, gw = walk.shape
    for j in range(gh):
        ny = j / max(gh - 1, 1)
        py = int(np.clip((1.0 - ny) * (h - 1), 0, h - 1))
        for i in range(gw):
            if not crate_grid[j, i]:
                continue
            nx = i / max(gw - 1, 1)
            px = int(np.clip(nx * (w - 1), 0, w - 1))
            walk[j, i] = False
            colors[j, i] = rgb[py, px].astype(np.uint8)


def downsample(walk: np.ndarray, gw: int, gh: int) -> np.ndarray:
    h, w = walk.shape
    ys = np.linspace(0, h - 1, gh).astype(int)
    xs = np.linspace(0, w - 1, gw).astype(int)
    out = np.zeros((gh, gw), dtype=bool)
    for j, y in enumerate(ys):
        for i, x in enumerate(xs):
            y0, y1 = max(0, y - 2), min(h, y + 3)
            x0, x1 = max(0, x - 2), min(w, x + 3)
            out[j, i] = walk[y0:y1, x0:x1].mean() > 0.35
    return out


def sample_cell_colors(rgb: np.ndarray, walk: np.ndarray, gw: int, gh: int) -> np.ndarray:
    h, w = rgb.shape[:2]
    orange = build_orange_exterior_mask(rgb)
    colors = np.full((gh, gw, 3), DEFAULT_BG_RGB, dtype=np.uint8)
    for j in range(gh):
        ny = j / max(gh - 1, 1)
        py = int(np.clip((1.0 - ny) * (h - 1), 0, h - 1))
        for i in range(gw):
            nx = i / max(gw - 1, 1)
            px = int(np.clip(nx * (w - 1), 0, w - 1))
            if orange[py, px]:
                colors[j, i] = DEFAULT_BG_RGB
            elif walk[j, i]:
                colors[j, i] = rgb[py, px]
            else:
                colors[j, i] = DEFAULT_BG_RGB
    return colors


def _snap_norm(walk: np.ndarray, nx: float, ny: float) -> tuple[float, float]:
    gh, gw = walk.shape
    i = int(np.clip(nx * (gw - 1), 0, gw - 1))
    j = int(np.clip(ny * (gh - 1), 0, gh - 1))
    if walk[j, i]:
        return i / max(gw - 1, 1), j / max(gh - 1, 1)
    for radius in range(1, 24):
        for dj in range(-radius, radius + 1):
            for di in range(-radius, radius + 1):
                ni, nj = i + di, j + dj
                if 0 <= ni < gw and 0 <= nj < gh and walk[nj, ni]:
                    return ni / max(gw - 1, 1), nj / max(gh - 1, 1)
    return nx, ny


def _centroid_norm(mask: np.ndarray) -> tuple[float, float]:
    if not mask.any():
        return 0.5, 0.5
    ys, xs = np.where(mask)
    h, w = mask.shape
    return xs.mean() / w, 1.0 - ys.mean() / h


def find_red_site(rgb: np.ndarray, site: str) -> tuple[float, float]:
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    if site == "A":
        mask = (r > 140) & (g < 100) & (b < 100) & (r > g + 40)
    else:
        mask = (r > 120) & (g < 90) & (b < 90)
        h = mask.shape[0]
        mask[int(h * 0.45) :, :] = False
    return _centroid_norm(mask)


def find_blue_spawn(rgb: np.ndarray) -> tuple[float, float]:
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    mask = (b > 100) & (r < 120) & (g < 140) & (b > r)
    return _centroid_norm(mask) if mask.any() else (0.15, 0.2)


def find_yellow_spawn(rgb: np.ndarray) -> tuple[float, float]:
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    mask = (r > 150) & (g > 120) & (b < 100)
    return _centroid_norm(mask) if mask.any() else (0.92, 0.55)


def find_connector(walk: np.ndarray, a_norm: tuple[float, float]) -> tuple[float, float]:
    ax, ay = a_norm
    gh, gw = walk.shape
    best = None
    best_score = -1.0
    for nx in np.linspace(ax + 0.04, min(ax + 0.18, 0.95), 24):
        for ny in np.linspace(ay - 0.06, ay + 0.06, 12):
            i = int(np.clip(nx * (gw - 1), 0, gw - 1))
            j = int(np.clip(ny * (gh - 1), 0, gh - 1))
            if not walk[j, i]:
                continue
            score = 1.0 - abs(ny - ay) + 0.5 * (nx - ax)
            if score > best_score:
                best_score = score
                best = (nx, ny)
    return best if best else (ax + 0.08, ay)


def find_jungle(walk: np.ndarray, conn_norm: tuple[float, float]) -> tuple[float, float]:
    cx, cy = conn_norm
    gh, gw = walk.shape
    best = None
    best_score = -1.0
    for nx in np.linspace(cx - 0.12, cx + 0.02, 18):
        for ny in np.linspace(cy + 0.02, min(cy + 0.14, 0.92), 14):
            i = int(np.clip(nx * (gw - 1), 0, gw - 1))
            j = int(np.clip(ny * (gh - 1), 0, gh - 1))
            if not walk[j, i]:
                continue
            score = ny - cy + 0.3 * (cx - nx)
            if score > best_score:
                best_score = score
                best = (nx, ny)
    return _snap_norm(walk, *(best or (cx - 0.03, cy + 0.06)))


def detect_cs2_sites(rgb: np.ndarray, walk: np.ndarray) -> tuple[list[ExplosionSource], list[MapMarker]]:
    a_norm = _snap_norm(walk, *find_red_site(rgb, "A"))
    b_norm = _snap_norm(walk, *find_red_site(rgb, "B"))
    ct_norm = _snap_norm(walk, *find_blue_spawn(rgb))
    t_norm = _snap_norm(walk, *find_yellow_spawn(rgb))
    conn_norm = _snap_norm(walk, *find_connector(walk, a_norm))
    j_norm = find_jungle(walk, conn_norm)

    sources = [ExplosionSource(id="bomb_a", norm=a_norm, label="C4", color="#ff6600")]
    markers = [
        MapMarker(id="B", norm=b_norm, label="B 包点", color="#cc5555"),
        MapMarker(id="connector", norm=conn_norm, label="链接", color="#66ccff"),
        MapMarker(id="jungle", norm=j_norm, label="Jungle", color="#66ff99"),
        MapMarker(id="ct", norm=ct_norm, label="CT 家", color="#6699ff"),
        MapMarker(id="t", norm=t_norm, label="T 家", color="#ffcc44"),
    ]
    return sources, markers


def import_from_radar_image(
    path: Path,
    *,
    map_name: str = "radar_import",
    grid_w: int = DEFAULT_GRID_W,
    grid_h: int = DEFAULT_GRID_H,
    cs2_mirage: bool = False,
    auto_sites: bool = True,
    detect_crates: bool = True,
) -> tuple[MapBundle, np.ndarray]:
    """One-click: radar PNG -> walkable grid + colors + CS2 sites + crate obstacles."""
    rgb = load_rgb(path)
    walk_full = build_walkability(rgb, cs2_mirage=cs2_mirage)
    walk = downsample(walk_full, grid_w, grid_h)
    colors = sample_cell_colors(rgb, walk, grid_w, grid_h)

    if detect_crates:
        crate_full = build_crate_mask(rgb, walk_full)
        crate_grid = downsample_mask(crate_full, grid_w, grid_h)
        apply_crate_obstacles(rgb, walk, colors, crate_grid)

    sources: list[ExplosionSource] = []
    markers: list[MapMarker] = []
    if auto_sites:
        sources, markers = detect_cs2_sites(rgb, walk)

    bundle = MapBundle(
        map_name=map_name,
        grid_w=grid_w,
        grid_h=grid_h,
        walkable=walk,
        cell_colors=colors,
        explosion_sources=sources,
        markers=markers,
    )
    return bundle, rgb


def save_editable_bundle(
    path: Path,
    *,
    map_name: str = "de_mirage_editable",
    cs2_mirage: bool = True,
) -> Path:
    """Import radar PNG and write a fully editable map folder."""
    bundle, rgb = import_from_radar_image(
        path,
        map_name=map_name,
        cs2_mirage=cs2_mirage,
        auto_sites=True,
        detect_crates=True,
    )
    out = bundle.save()
    ref_path = out / "reference.png"
    Image.fromarray(rgb).save(ref_path)
    return out


def import_mirage_radar(name: str = "de_mirage") -> MapBundle:
    if not _MIRAGE_RADAR.exists():
        raise FileNotFoundError(f"Mirage radar not found: {_MIRAGE_RADAR}")
    bundle, _ = import_from_radar_image(
        _MIRAGE_RADAR,
        map_name=name,
        cs2_mirage=True,
        auto_sites=True,
    )
    return bundle


def mirage_radar_path() -> Path:
    return _MIRAGE_RADAR
