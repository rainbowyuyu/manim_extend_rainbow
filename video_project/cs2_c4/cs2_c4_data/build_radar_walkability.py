#!/usr/bin/env python3
"""Build walkability grid and site positions from Mirage radar PNG + official overview."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

try:
    from PIL import Image
except ImportError:
    raise SystemExit("pip install pillow")

ROOT = Path(__file__).resolve().parents[1]
RADAR = ROOT / "assets" / "de_mirage_radar.png"
OUT_DIR = ROOT / "cs2_c4_data"
OVERVIEW = OUT_DIR / "de_mirage_overview.txt"
GRID_W, GRID_H = 128, 96

_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from yty_manim.basic_unit.cs2_map import load_mirage_overview
from yty_manim.tools.map_editor.map_radar_import import build_orange_exterior_mask


def load_radar() -> np.ndarray:
    img = Image.open(RADAR).convert("RGB")
    return np.array(img)


def build_walkability(rgb: np.ndarray) -> np.ndarray:
    """Gray floor = walkable; black = wall. Colored zones (sites/spawns) forced walkable."""
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    lum = 0.299 * r + 0.587 * g + 0.114 * b
    walk = lum > 28
    # bomb sites (red), CT (blue), T (yellow) overlays
    red_site = (r > 100) & (g < 110) & (b < 110) & (r > g + 25)
    blue_spawn = (b > 90) & (r < 130) & (g < 150) & (b > r)
    yellow_spawn = (r > 140) & (g > 110) & (b < 110)
    walk = walk | red_site | blue_spawn | yellow_spawn
    walk &= ~build_orange_exterior_mask(rgb)
    h, w = walk.shape
    walk[int(h * 0.88) :, int(w * 0.72) :] = False
    return walk


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


def find_red_centroid(rgb: np.ndarray, label: str) -> tuple[float, float]:
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    if label == "A":
        mask = (r > 140) & (g < 100) & (b < 100) & (r > g + 40)
    else:  # B
        mask = (r > 120) & (g < 90) & (b < 90)
        # B is upper-left — exclude A region (bottom)
        h = mask.shape[0]
        mask[int(h * 0.45) :, :] = False
    if not mask.any():
        return 0.5, 0.5
    ys, xs = np.where(mask)
    cy, cx = ys.mean(), xs.mean()
    h, w = rgb.shape[:2]
    return cx / w, 1.0 - cy / h  # norm: origin bottom-left


def find_blue_spawn(rgb: np.ndarray) -> tuple[float, float]:
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    mask = (b > 100) & (r < 120) & (g < 140) & (b > r)
    if not mask.any():
        return 0.15, 0.2
    ys, xs = np.where(mask)
    h, w = rgb.shape[:2]
    return xs.mean() / w, 1.0 - ys.mean() / h


def find_yellow_spawn(rgb: np.ndarray) -> tuple[float, float]:
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    mask = (r > 150) & (g > 120) & (b < 100)
    if not mask.any():
        return 0.92, 0.55
    ys, xs = np.where(mask)
    h, w = rgb.shape[:2]
    return xs.mean() / w, 1.0 - ys.mean() / h


def find_connector(walk: np.ndarray, a_norm: tuple[float, float]) -> tuple[float, float]:
    """链接：A 点东侧走廊中点。"""
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


def find_jungle(walk: np.ndarray, conn_norm: tuple[float, float], ct_norm: tuple[float, float]) -> tuple[float, float]:
    """Jungle：链接偏西北、靠近中路一侧。"""
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
    return snap_to_walkable_norm(walk, *(best or (cx - 0.03, cy + 0.06)))


def snap_to_walkable_norm(walk: np.ndarray, nx: float, ny: float) -> tuple[float, float]:
    gh, gw = walk.shape
    i = int(np.clip(nx * (gw - 1), 0, gw - 1))
    j = int(np.clip(ny * (gh - 1), 0, gh - 1))
    if walk[j, i]:
        return i / (gw - 1), j / (gh - 1)
    for radius in range(1, 24):
        for dj in range(-radius, radius + 1):
            for di in range(-radius, radius + 1):
                ni, nj = i + di, j + dj
                if 0 <= ni < gw and 0 <= nj < gh and walk[nj, ni]:
                    return ni / (gw - 1), nj / (gh - 1)
    return nx, ny


def sample_cell_colors(rgb: np.ndarray, walk: np.ndarray) -> np.ndarray:
    """Per-grid-cell RGB sampled from radar (for vector floor)."""
    h, w = rgb.shape[:2]
    gh, gw = walk.shape
    colors = np.zeros((gh, gw, 3), dtype=np.uint8)
    for j in range(gh):
        ny = j / max(gh - 1, 1)
        py = int(np.clip((1.0 - ny) * (h - 1), 0, h - 1))
        for i in range(gw):
            if not walk[j, i]:
                continue
            nx = i / max(gw - 1, 1)
            px = int(np.clip(nx * (w - 1), 0, w - 1))
            colors[j, i] = rgb[py, px]
    return colors


def main() -> None:
    if not RADAR.exists():
        raise FileNotFoundError(RADAR)
    rgb = load_radar()
    walk_full = build_walkability(rgb)
    walk = downsample(walk_full, GRID_W, GRID_H)

    a_norm = snap_to_walkable_norm(walk, *find_red_centroid(rgb, "A"))
    b_norm = snap_to_walkable_norm(walk, *find_red_centroid(rgb, "B"))
    ct_norm = snap_to_walkable_norm(walk, *find_blue_spawn(rgb))
    t_norm = snap_to_walkable_norm(walk, *find_yellow_spawn(rgb))
    conn_norm = snap_to_walkable_norm(walk, *find_connector(walk, a_norm))
    j_norm = find_jungle(walk, conn_norm, ct_norm)

    overview = load_mirage_overview(OVERVIEW if OVERVIEW.exists() else None)
    official = overview.official_sites_scene_norm() if OVERVIEW.exists() else {}

    meta = {
        "grid_w": GRID_W,
        "grid_h": GRID_H,
        "overview": {
            "pos_x": overview.pos_x,
            "pos_y": overview.pos_y,
            "scale": overview.scale,
            "radar_size": 1024,
            "source": "Valve resource/overviews/de_mirage.txt",
            "official_sites_norm": {k: list(v) for k, v in official.items()},
        },
        "sites": {
            "A": {"norm": list(a_norm), "label": "A 包点"},
            "B": {"norm": list(b_norm), "label": "B 包点"},
            "connector": {"norm": list(conn_norm), "label": "链接"},
            "jungle": {"norm": list(j_norm), "label": "Jungle"},
            "ct": {"norm": list(ct_norm), "label": "CT 家"},
            "t": {"norm": list(t_norm), "label": "T 家"},
        },
        "radar_source": str(RADAR),
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    np.save(OUT_DIR / "mirage_walkable.npy", walk)
    np.save(OUT_DIR / "mirage_cell_colors.npy", sample_cell_colors(rgb, walk))
    (OUT_DIR / "mirage_radar_meta.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"walkable cells: {walk.sum()} / {walk.size}")
    print(json.dumps(meta["sites"], indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
