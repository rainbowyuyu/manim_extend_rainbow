# rainbow_yu manim_extend.basic_unit.cs2_map 🐋✨
# CS2 地图：Mirage 数据/渲染、MapBundle 视图、引擎文案常量

from __future__ import annotations

import heapq
import json
import re
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from manim import *
from scipy.ndimage import zoom

from yty_manim.disposition.fonts_and_colors import (
    cs2_bundle_map,
    cs2_map_heat,
    cs2_map_physics,
    cs2_mirage_map,
)
from yty_manim.tools.map_editor.map_bundle import ExplosionSource, MapBundle, MapMarker
from yty_manim.tools.map_editor.map_wave import shockwave_field

__all__ = (
    "WAVE_SPEED_M_S",
    "intensity_color",
    "MirageVectorMap",
    "GridMapView",
    "MirageOverview",
    "MapSite",
    "bind_fluid_wave_tracker",
    "bind_wave_tracker",
    "build_map_view_from_bundle",
    "load_mirage_overview",
    "shockwave_field",
    "dijkstra_wave_field",
    "arrival_time_seconds",
)



# ── 引擎文案常量 ────────────────────────────────────────────

GAMEINFO_BOMB_PIPELINE = '''\
GameSpecificPostMapBuildSteps
{
    "cs2_bomb_damage"      "1"
}'''

GAMEINFO_PATH = r"game\csgo_core\gameinfo.gi"

VPK_BOMB_RESOURCE = "maps/de_mirage/baked_bomb_damage.vdata"

# Inferred propagation speed (arrival = path_meters / WAVE_SPEED); aligns with ~33–77 m lethal radius timing

VPK_BOMB_RESOURCE_ALT = "content/csgo/maps/de_mirage/baked_bomb_damage.vdata"

DEBUG_CONSOLE = "cl_bake_bomb_damage_debug 1"

UI_SETTINGS = '"settings_damage_prediction"'

SOUND_ASSET = 'name = "C4Shockwave"'

PATCH_NOTES_EN = (
    "Damage is now applied according to precomputed simulation values, "
    "baked into the compiled map."
)

RUNTIME_PSEUDOCODE = '''\
// Runtime (inferred from official behavior)
float wave_front = g_flBombDetonateTime + (t - t0) * WAVE_SPEED;
float wave_dist  = baked_field[pos.site][pos.cell].arrival;
float power      = baked_field[pos.site][pos.cell].damage_power;

if (wave_front >= wave_dist) {
    ApplyDamage(player, power);
}

// UI preview (same table, before detonation)
preview_hp = player.health - power;'''

# Step-by-step panels for MirageShockwaveDemoScene
RUNTIME_CODE_STEPS: list[tuple[str, str]] = [
    (
        "① 波前推进",
        "float wave_front = g_flBombDetonateTime\n"
        "                 + (t - t0) * WAVE_SPEED;",
    ),
    (
        "② 查表 baked_field",
        "float wave_dist = field[pos].arrival;\n"
        "float power     = field[pos].damage_power;",
    ),
    (
        "③ 到达才结算",
        "if (wave_front >= wave_dist) {\n"
        "    ApplyDamage(player, power);\n"
        "}",
    ),
    (
        "④ 血条预览",
        "preview_hp = player.health - power;",
    ),
]

BAKE_PSEUDOCODE = '''\
// Map compile: cs2_bomb_damage post-step
for each walkable cell c in nav_mesh:
    dist[c] = DijkstraWave(bombsite_A, c, walls);
    field[c].arrival     = dist[c] / WAVE_SPEED;
    field[c].damage_power = Falloff(dist[c], corners);
Save("maps/de_mirage/baked_bomb_damage.vdata");'''

RECORD_CFG_SNIPPET = '''\
sv_cheats 1
cl_bake_bomb_damage_debug 1'''

# ── 热力着色 ────────────────────────────────────────────────


def intensity_color(
    t: float,
    *,
    cool: str = cs2_map_heat["C_WAVE_COOL"],
    mid: str = cs2_map_heat["C_WAVE_MID"],
    hot: str = cs2_map_heat["C_WAVE_HOT"],
    zero: str | None = cs2_map_heat["C_WALK"],
) -> str:
    """t∈[0,1] → hex；t<=0 时返回 zero（若给定）。"""
    t = float(t)
    if t <= 0 and zero is not None:
        return zero
    t = float(np.clip(t, 0.0, 1.0))
    if t < 0.35:
        c = interpolate_color(ManimColor(cool), ManimColor(mid), t / 0.35)
    else:
        c = interpolate_color(ManimColor(mid), ManimColor(hot), (t - 0.35) / 0.65)
    return c.to_hex()


# ── Mirage 数据 ──────────────────────────────────────────────

# Baked damage from CS2 baked_bomb_damage.vdata (see parse_baked_bomb_damage.py).
# Coordinates: normalized [0, 1] × [0, 1], origin bottom-left.



MAP_NAME = "de_mirage"

_DATA_DIR = Path(__file__).resolve().parents[2] / "video_project" / "cs2_c4" / "cs2_c4_data"
_ASSETS_DIR = Path(__file__).resolve().parents[2] / "video_project" / "cs2_c4" / "assets"
RADAR_IMAGE = _ASSETS_DIR / "de_mirage_radar.png"
WALKABLE_NPY = _DATA_DIR / "mirage_walkable.npy"
RADAR_META = _DATA_DIR / "mirage_radar_meta.json"
BAKED_NPZ = _DATA_DIR / "mirage_baked_site_a.npz"
BAKED_META = _DATA_DIR / "mirage_baked_site_a_meta.json"

# Grid from radar downsample (128×96)
GRID_W, GRID_H = cs2_map_physics["GRID_W"], cs2_map_physics["GRID_H"]

# From baked_bomb_damage pseudocode (arrival = dist / WAVE_SPEED)
CELL_METERS = cs2_map_physics["CELL_METERS"]
WAVE_SPEED_M_S = cs2_map_physics["WAVE_SPEED_M_S"]
WAVE_SPEED_GRID = WAVE_SPEED_M_S / CELL_METERS


@dataclass(frozen=True)
class MapSite:
    name: str
    norm: tuple[float, float]
    label_cn: str


def _load_meta() -> dict:
    if not RADAR_META.exists():
        raise FileNotFoundError(
            f"Missing {RADAR_META}. Run video_project/cs2_c4/cs2_c4_data/build_radar_walkability.py"
        )
    return json.loads(RADAR_META.read_text(encoding="utf-8"))


def _site(key: str, meta: dict) -> MapSite:
    s = meta["sites"][key]
    return MapSite(key, tuple(s["norm"]), s["label"])


_meta = _load_meta()
GRID_W = int(_meta.get("grid_w", GRID_W))
GRID_H = int(_meta.get("grid_h", GRID_H))

BOMB_SITE_A = _site("A", _meta)
BOMB_SITE_B = _site("B", _meta)
CONNECTOR = _site("connector", _meta)
JUNGLE = _site("jungle", _meta)
CT_SPAWN = _site("ct", _meta)
T_SPAWN = _site("t", _meta)

MARKERS = (BOMB_SITE_A, BOMB_SITE_B, CONNECTOR, JUNGLE, CT_SPAWN, T_SPAWN)
DEMO_MARKERS = (BOMB_SITE_A, CONNECTOR, JUNGLE, CT_SPAWN)


def _load_walkable() -> np.ndarray:
    if not WALKABLE_NPY.exists():
        raise FileNotFoundError(
            f"Missing {WALKABLE_NPY}. Run build_radar_walkability.py first."
        )
    walk = np.load(WALKABLE_NPY)
    if walk.shape != (GRID_H, GRID_W):
        raise ValueError(f"Expected walkable shape ({GRID_H}, {GRID_W}), got {walk.shape}")
    return walk.astype(bool)


CELL_COLORS_NPY = _DATA_DIR / "mirage_cell_colors.npy"


def _load_cell_colors() -> np.ndarray | None:
    if not CELL_COLORS_NPY.exists():
        return None
    colors = np.load(CELL_COLORS_NPY)
    if colors.shape != (GRID_H, GRID_W, 3):
        return None
    return colors


WALKABLE = _load_walkable()
CELL_COLORS = _load_cell_colors()


def rgb_to_hex(r: int, g: int, b: int) -> str:
    return f"#{r:02x}{g:02x}{b:02x}"


def norm_to_grid(nx: float, ny: float) -> tuple[int, int]:
    i = int(np.clip(nx * (GRID_W - 1), 0, GRID_W - 1))
    j = int(np.clip(ny * (GRID_H - 1), 0, GRID_H - 1))
    return i, j


def grid_to_norm(i: int, j: int) -> tuple[float, float]:
    return i / (GRID_W - 1), j / (GRID_H - 1)


def grid_dist_to_meters(d: float) -> float:
    return d * CELL_METERS


def arrival_time_seconds(path_dist_grid: float) -> float:
    """Matches bake pseudocode: field[c].arrival = dist[c] / WAVE_SPEED."""
    return grid_dist_to_meters(path_dist_grid) / WAVE_SPEED_M_S


def _snap_walkable(i: int, j: int) -> tuple[int, int]:
    if WALKABLE[j, i]:
        return i, j
    for radius in range(1, 12):
        for dj in range(-radius, radius + 1):
            for di in range(-radius, radius + 1):
                ni, nj = i + di, j + dj
                if 0 <= ni < GRID_W and 0 <= nj < GRID_H and WALKABLE[nj, ni]:
                    return ni, nj
    return i, j


def dijkstra_wave_field(source_norm: tuple[float, float]) -> tuple[np.ndarray, np.ndarray]:
    """Returns (dist_grid, intensity_grid). Unreachable = inf / 0."""
    si, sj = norm_to_grid(*source_norm)
    si, sj = _snap_walkable(si, sj)

    dist = np.full((GRID_H, GRID_W), np.inf, dtype=float)
    dist[sj, si] = 0.0
    pq: list[tuple[float, int, int]] = [(0.0, si, sj)]
    moves = [
        (1, 0, 1.0), (-1, 0, 1.0), (0, 1, 1.0), (0, -1, 1.0),
        (1, 1, 1.414), (1, -1, 1.414), (-1, 1, 1.414), (-1, -1, 1.414),
    ]

    while pq:
        d, i, j = heapq.heappop(pq)
        if d > dist[j, i]:
            continue
        for di, dj, cost in moves:
            ni, nj = i + di, j + dj
            if 0 <= ni < GRID_W and 0 <= nj < GRID_H and WALKABLE[nj, ni]:
                nd = d + cost
                if nd < dist[nj, ni]:
                    dist[nj, ni] = nd
                    heapq.heappush(pq, (nd, ni, nj))

    finite = dist[np.isfinite(dist)]
    max_d = float(finite.max()) if finite.size else 1.0
    intensity = np.zeros_like(dist)
    mask = np.isfinite(dist)
    # Normalized falloff; calibrated so sample points align with SkinSniper 20%/40% bands
    intensity[mask] = np.clip(1.0 - dist[mask] / max_d, 0, 1)
    intensity[mask] = intensity[mask] ** 0.82
    return dist, intensity


def _load_baked_damage() -> tuple[np.ndarray | None, np.ndarray | None, np.ndarray | None]:
    if not BAKED_NPZ.exists():
        return None, None, None
    data = np.load(BAKED_NPZ)
    grid = data["damage_power"]
    if grid.shape != (GRID_H, GRID_W):
        raise ValueError(f"Expected baked shape ({GRID_H}, {GRID_W}), got {grid.shape}")
    cell_norms = data["cell_norms"] if "cell_norms" in data else None
    cell_power = data["cell_power"] if "cell_power" in data else None
    return grid.astype(np.uint8), cell_norms, cell_power


_baked = _load_baked_damage()
BAKED_DAMAGE, BAKED_CELL_NORMS, BAKED_CELL_POWER = _baked
HAS_BAKED_DAMAGE = BAKED_DAMAGE is not None


def _build_baked_lookup_grid() -> np.ndarray:
    """Rasterize baked damage onto radar grid (KD-tree, aligned with walkability)."""
    grid = np.zeros((GRID_H, GRID_W), dtype=np.float32)
    if BAKED_CELL_NORMS is None or BAKED_CELL_POWER is None:
        if BAKED_DAMAGE is not None:
            mask = WALKABLE & (BAKED_DAMAGE > 0)
            grid[mask] = BAKED_DAMAGE[mask].astype(np.float32) / 255.0
        return grid
    try:
        from scipy.spatial import cKDTree

        tree = cKDTree(BAKED_CELL_NORMS)
        norms: list[tuple[float, float]] = []
        cells: list[tuple[int, int]] = []
        for j in range(GRID_H):
            for i in range(GRID_W):
                if WALKABLE[j, i]:
                    norms.append(grid_to_norm(i, j))
                    cells.append((j, i))
        if not norms:
            return grid
        pts = np.array(norms, dtype=np.float32)
        dists, idxs = tree.query(pts, k=1)
        for (j, i), d, idx in zip(cells, dists, idxs):
            if d <= 0.035:
                grid[j, i] = float(BAKED_CELL_POWER[idx]) / 255.0
    except ImportError:
        mask = WALKABLE & (BAKED_DAMAGE > 0) if BAKED_DAMAGE is not None else WALKABLE
        if BAKED_DAMAGE is not None:
            grid[mask] = BAKED_DAMAGE[mask].astype(np.float32) / 255.0
    return grid


BAKED_INTENSITY_LOOKUP = _build_baked_lookup_grid()


def _nearest_baked_power(norm: tuple[float, float]) -> int:
    if BAKED_CELL_NORMS is None or BAKED_CELL_POWER is None:
        i, j = norm_to_grid(*norm)
        i, j = _snap_walkable(i, j)
        return int(BAKED_DAMAGE[j, i]) if BAKED_DAMAGE is not None else 0
    try:
        from scipy.spatial import cKDTree

        tree = cKDTree(BAKED_CELL_NORMS)
        dist, idx = tree.query(norm, k=1)
        if dist > 0.03:
            return 0
        return int(BAKED_CELL_POWER[idx])
    except ImportError:
        d = np.linalg.norm(BAKED_CELL_NORMS - np.array(norm), axis=1)
        idx = int(np.argmin(d))
        if d[idx] > 0.03:
            return 0
        return int(BAKED_CELL_POWER[idx])


def damage_power_to_intensity(power: int | float | np.ndarray) -> float | np.ndarray:
    if isinstance(power, np.ndarray):
        return np.clip(power.astype(np.float64) / 255.0, 0.0, 1.0)
    return float(np.clip(float(power) / 255.0, 0.0, 1.0))


def baked_intensity_field(dist: np.ndarray) -> np.ndarray:
    if BAKED_DAMAGE is None and BAKED_INTENSITY_LOOKUP.max() <= 0:
        raise FileNotFoundError(
            f"Missing {BAKED_NPZ}. Run parse_baked_bomb_damage.py first."
        )
    out = np.zeros_like(dist, dtype=float)
    mask = np.isfinite(dist) & WALKABLE
    out[mask] = BAKED_INTENSITY_LOOKUP[mask]
    return out


def shockwave_field(
    source_norm: tuple[float, float] = BOMB_SITE_A.norm,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Returns (dist_grid, intensity_grid, damage_power_grid)."""
    dist, fallback_intensity = dijkstra_wave_field(source_norm)
    if BAKED_DAMAGE is not None:
        intensity = baked_intensity_field(dist)
        damage = BAKED_DAMAGE.astype(np.int32)
    else:
        intensity = fallback_intensity
        damage = np.zeros((GRID_H, GRID_W), dtype=np.int32)
        mask = np.isfinite(dist)
        damage[mask] = intensity_to_damage(intensity[mask])
    return dist, intensity, damage


def intensity_to_damage(intensity: float) -> int:
    """Fallback when baked grid is missing."""
    if intensity <= 0:
        return 0
    if intensity >= 1.0:
        return 255
    if intensity <= 0.2:
        return int(165 * intensity)
    if intensity <= 0.4:
        return int(33 + (intensity - 0.2) * 220)
    if intensity <= 0.7:
        return int(77 + (intensity - 0.4) * 200)
    return int(137 + (intensity - 0.7) * 393)


def damage_power_from_dist(path_dist_grid: float, max_dist_grid: float) -> int:
    if not np.isfinite(path_dist_grid) or max_dist_grid <= 0:
        return 0
    inten = max(0.0, 1.0 - path_dist_grid / max_dist_grid) ** 0.82
    return intensity_to_damage(inten)


def sample_at(
    site: MapSite,
    dist: np.ndarray,
    intensity: np.ndarray,
    damage: np.ndarray | None = None,
) -> tuple[float, float, int, float]:
    i, j = norm_to_grid(*site.norm)
    i, j = _snap_walkable(i, j)
    d = float(dist[j, i]) if np.isfinite(dist[j, i]) else float("inf")
    if damage is not None and HAS_BAKED_DAMAGE:
        baked = _nearest_baked_power(site.norm)
        if baked > 0:
            dmg = baked
            inten = damage_power_to_intensity(dmg)  # type: ignore[assignment]
            return d, float(inten), dmg, arrival_time_seconds(d)
    if damage is not None and damage[j, i] > 0:
        dmg = int(damage[j, i])
        inten = damage_power_to_intensity(dmg)
    else:
        inten = float(intensity[j, i]) if np.isfinite(d) else 0.0
        dmg = intensity_to_damage(inten)
    return d, inten, dmg, arrival_time_seconds(d)

# ── Overview 坐标 ────────────────────────────────────────────


_OVERVIEW_PATH = (
    Path(__file__).resolve().parents[2]
    / "video_project"
    / "cs2_c4"
    / "cs2_c4_data"
    / "de_mirage_overview.txt"
)

RADAR_SIZE = cs2_map_physics["RADAR_SIZE"]  # standard CS2 overview texture


@dataclass(frozen=True)
class MirageOverview:
    pos_x: float
    pos_y: float
    scale: float
    rotate: float
    zoom: float
    inset_left: float
    inset_top: float
    inset_right: float
    inset_bottom: float
    ct_spawn: tuple[float, float]
    t_spawn: tuple[float, float]
    bomb_a: tuple[float, float]
    bomb_b: tuple[float, float]

    @property
    def world_width(self) -> float:
        return self.scale * RADAR_SIZE

    @property
    def world_height(self) -> float:
        return self.scale * RADAR_SIZE

    def world_to_radar_px(self, wx: float, wy: float) -> tuple[float, float]:
        """World XY → radar image pixel (origin top-left, y down)."""
        px = (wx - self.pos_x) / self.scale
        py = (self.pos_y - wy) / self.scale
        return px, py

    def radar_px_to_world(self, px: float, py: float) -> tuple[float, float]:
        wx = px * self.scale + self.pos_x
        wy = self.pos_y - py * self.scale
        return wx, wy

    def overview_norm_to_scene_norm(self, ox: float, oy: float) -> tuple[float, float]:
        """Overview icon coords (top-left 0–1) → scene norm (bottom-left 0–1)."""
        il, it, ir, ib = self.inset_left, self.inset_top, self.inset_right, self.inset_bottom
        inner_w = 1.0 - il - ir
        inner_h = 1.0 - it - ib
        nx = il + ox * inner_w
        ny = 1.0 - (it + oy * inner_h)
        return nx, ny

    def official_sites_scene_norm(self) -> dict[str, tuple[float, float]]:
        return {
            "A": self.overview_norm_to_scene_norm(*self.bomb_a),
            "B": self.overview_norm_to_scene_norm(*self.bomb_b),
            "ct": self.overview_norm_to_scene_norm(*self.ct_spawn),
            "t": self.overview_norm_to_scene_norm(*self.t_spawn),
        }


def _parse_overview_text(text: str) -> MirageOverview:
    def _f(key: str, default: float = 0.0) -> float:
        m = re.search(rf'"{key}"\s+"([^"]+)"', text)
        return float(m.group(1)) if m else default

    return MirageOverview(
        pos_x=_f("pos_x"),
        pos_y=_f("pos_y"),
        scale=_f("scale", 5.0),
        rotate=_f("rotate"),
        zoom=_f("zoom"),
        inset_left=_f("inset_left", 0.135),
        inset_top=_f("inset_top", 0.08),
        inset_right=_f("inset_right", 0.105),
        inset_bottom=_f("inset_bottom", 0.08),
        ct_spawn=(_f("CTSpawn_x"), _f("CTSpawn_y")),
        t_spawn=(_f("TSpawn_x"), _f("TSpawn_y")),
        bomb_a=(_f("bombA_x"), _f("bombA_y")),
        bomb_b=(_f("bombB_x"), _f("bombB_y")),
    )


def load_mirage_overview(path: Path | None = None) -> MirageOverview:
    p = path or _OVERVIEW_PATH
    return _parse_overview_text(p.read_text(encoding="utf-8"))


MIRAGE_OVERVIEW = load_mirage_overview()

# ── Mirage 矢量地图 ──────────────────────────────────────────

# Mirage 矢量地图默认值（独立 C_BG，避免被 MapBundle 段覆盖）
MAP_W, MAP_H = cs2_mirage_map["MAP_W"], cs2_mirage_map["MAP_H"]
C_BG = cs2_mirage_map["C_BG"]
C_FLOOR_EDGE = cs2_mirage_map["C_FLOOR_EDGE"]
C_WALK = cs2_mirage_map["C_WALK"]
C_WAVE_HOT = cs2_mirage_map["C_WAVE_HOT"]
C_WAVE_MID = cs2_mirage_map["C_WAVE_MID"]
C_WAVE_COOL = cs2_mirage_map["C_WAVE_COOL"]
C_GLOW = cs2_mirage_map["C_GLOW"]
CELL_GAP = cs2_mirage_map["CELL_GAP"]
WAVE_UPSAMPLE = cs2_mirage_map["WAVE_UPSAMPLE"]
MAX_CONTOUR_PTS = cs2_mirage_map["MAX_CONTOUR_PTS"]
RADIUS_QUANT = cs2_mirage_map["RADIUS_QUANT"]


def _intensity_color(t: float) -> str:
    return intensity_color(t, cool=C_WAVE_COOL, mid=C_WAVE_MID, hot=C_WAVE_HOT, zero=C_WALK)


def _norm_to_scene(nx: float, ny: float) -> np.ndarray:
    return np.array([nx * MAP_W - MAP_W / 2, ny * MAP_H - MAP_H / 2, 0.0])


def _cell_center_norm(i: int, j: int) -> tuple[float, float]:
    return i / (GRID_W - 1), j / (GRID_H - 1)


def _cell_size() -> tuple[float, float]:
    return MAP_W / GRID_W * (1.0 - CELL_GAP), MAP_H / GRID_H * (1.0 - CELL_GAP)


def _make_cell_rect(i: int, j: int, color: str, **kw) -> Rectangle:
    cw, ch = _cell_size()
    rect = Rectangle(width=cw, height=ch, fill_color=color, **kw)
    rect.move_to(_norm_to_scene(*_cell_center_norm(i, j)))
    return rect


def _upsample_field(field: np.ndarray, factor: int) -> np.ndarray:
    base = np.where(np.isfinite(field), field, 0.0)
    out = zoom(base, factor, order=1).astype(float)
    walk_hi = zoom(WALKABLE.astype(float), factor, order=0) > 0.5
    out[~walk_hi] = np.nan
    return out


def _decimate(pts: np.ndarray) -> np.ndarray:
    if len(pts) <= MAX_CONTOUR_PTS:
        return pts
    idx = np.linspace(0, len(pts) - 1, MAX_CONTOUR_PTS, dtype=int)
    return pts[idx]


def _contour_front_loops(field: np.ndarray, level: float) -> list[np.ndarray]:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    gh, gw = field.shape
    display = np.flipud(np.nan_to_num(field, nan=-1e9))
    fig = plt.figure()
    ax = fig.add_axes([0, 0, 1, 1])
    cs = ax.contour(display, levels=[level])
    loops = []
    for path in cs.get_paths():
        if len(path.vertices) < 3:
            continue
        pts = []
        for col, row_top in path.vertices:
            nx = np.clip(col / max(gw - 1, 1), 0, 1)
            ny = np.clip(1.0 - row_top / max(gh - 1, 1), 0, 1)
            pts.append(_norm_to_scene(nx, ny)[:2])
        loops.append(_decimate(np.array(pts)))
    plt.close(fig)
    return loops


class MirageVectorMap(VGroup):
    """
    Mirage 矢量俯视地图与流体冲击波前，
    继承于 :class:`~.VGroup` ，

    Notes
    -----

    - 数据来自同模块的可走栅格 / 站点常量
    - 用 :func:`bind_fluid_wave_tracker` 绑定半径追踪器

    """

    def __init__(
        self,
        dist: np.ndarray | None = None,
        intensity: np.ndarray | None = None,
        wave_radius: float | None = None,
        cell_opacity: float = 0.78,
        show_wave_front: bool = True,
        wave_front_band: float = 0.55,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.dist_field = dist
        self.intensity_field = intensity
        self.wave_radius = wave_radius
        self._cell_opacity = cell_opacity
        self._show_wave_front = show_wave_front
        self._wave_front_band = wave_front_band
        self._last_front_q: float | None = None

        factor = WAVE_UPSAMPLE
        self._dist_hi = _upsample_field(dist, factor) if dist is not None else None

        self.bg = Rectangle(
            width=MAP_W, height=MAP_H,
            fill_color=C_BG, fill_opacity=1,
            stroke_color=GREY_B, stroke_width=2.0,
        )
        self.floor = self._build_floor()
        self.heat, self._heat_cells = self._init_heat_layer()
        self.wave_front = VGroup()
        self.add(self.bg, self.floor, self.heat, self.wave_front)
        self.set_wave_radius(wave_radius)

    def _floor_color(self, i: int, j: int) -> str:
        if CELL_COLORS is None:
            return "#48484e"
        r, g, b = (int(v) for v in CELL_COLORS[j, i])
        lum = 0.299 * r + 0.587 * g + 0.114 * b
        if lum < 24:
            return C_BG
        return rgb_to_hex(int(r * 0.82 + 38), int(g * 0.82 + 38), int(b * 0.82 + 42))

    def _build_floor(self) -> VGroup:
        cells = VGroup()
        for j in range(GRID_H):
            for i in range(GRID_W):
                if not WALKABLE[j, i]:
                    continue
                cells.add(_make_cell_rect(
                    i, j, self._floor_color(i, j),
                    fill_opacity=0.94, stroke_width=0.35, stroke_color=C_FLOOR_EDGE,
                ))
        return cells

    def _init_heat_layer(self) -> tuple[VGroup, dict[tuple[int, int], Rectangle]]:
        cells = VGroup()
        index: dict[tuple[int, int], Rectangle] = {}
        for j in range(GRID_H):
            for i in range(GRID_W):
                if not WALKABLE[j, i]:
                    continue
                rect = _make_cell_rect(i, j, C_WALK, fill_opacity=0.0, stroke_width=0.0)
                cells.add(rect)
                index[(i, j)] = rect
        return cells, index

    def _update_smooth_front(self, radius: float) -> None:
        q = round(radius / RADIUS_QUANT) * RADIUS_QUANT
        if q == self._last_front_q:
            return
        self._last_front_q = q
        self.wave_front.submobjects.clear()
        if not self._show_wave_front or self._dist_hi is None or q <= 0:
            return
        for loop in _contour_front_loops(self._dist_hi, q):
            if len(loop) < 3:
                continue
            verts = [np.array([x, y, 0.0]) for x, y in loop]
            poly = Polygon(*verts, stroke_color=C_GLOW, stroke_width=2.8, stroke_opacity=0.95)
            poly.set_fill(opacity=0)
            self.wave_front.add(poly)

    def set_wave_radius(self, radius: float | None) -> None:
        self.wave_radius = radius
        has_field = self.intensity_field is not None and self.dist_field is not None
        op = self._cell_opacity

        for (i, j), rect in self._heat_cells.items():
            if not has_field:
                rect.set_fill(opacity=0.0)
                continue
            d = self.dist_field[j, i]
            if not np.isfinite(d) or (radius is not None and d > radius):
                rect.set_fill(opacity=0.0)
                continue
            t = float(self.intensity_field[j, i])
            if t <= 0:
                rect.set_fill(opacity=0.0)
                continue
            rect.set_fill(_intensity_color(t), opacity=op)

        if has_field and radius is not None and radius > 0:
            self._update_smooth_front(float(radius))
        else:
            self._last_front_q = None
            self.wave_front.submobjects.clear()

    def make_marker(self, site, color=YELLOW, label: str = "") -> VGroup:
        pos = _norm_to_scene(*site.norm)
        ring = Circle(radius=0.1, color=color, stroke_width=2.5).move_to(pos)
        dot = Dot(pos, radius=0.055, color=color)
        grp: Mobject = VGroup(ring, dot)
        if label:
            tag = Text(label, font="Sans", font_size=12, color=color)
            tag.next_to(ring, DOWN, buff=0.06)
            grp = VGroup(grp, tag)
        return grp


def bind_fluid_wave_tracker(mirage: MirageVectorMap, wave_t: ValueTracker) -> MirageVectorMap:
    mirage.set_wave_radius(wave_t.get_value())
    mirage.add_updater(lambda m: m.set_wave_radius(wave_t.get_value()))
    return mirage

# ── MapBundle 网格视图 ───────────────────────────────────────



# MapBundle 视图：使用独立前缀，避免覆盖 Mirage 的 C_BG
BUNDLE_MAP_W, BUNDLE_MAP_H = cs2_bundle_map["MAP_W"], cs2_bundle_map["MAP_H"]
BUNDLE_C_BG = cs2_bundle_map["C_BG"]
BUNDLE_C_FLOOR_EDGE = cs2_bundle_map["C_FLOOR_EDGE"]
BUNDLE_C_WALK = cs2_bundle_map["C_WALK"]
BUNDLE_C_WAVE_HOT = cs2_bundle_map["C_WAVE_HOT"]
BUNDLE_C_WAVE_MID = cs2_bundle_map["C_WAVE_MID"]
BUNDLE_C_WAVE_COOL = cs2_bundle_map["C_WAVE_COOL"]
BUNDLE_C_GLOW = cs2_bundle_map["C_GLOW"]
BUNDLE_CELL_GAP = cs2_bundle_map["CELL_GAP"]






class GridMapView(VGroup):
    """
    通用 MapBundle 网格地图视图，
    继承于 :class:`~.VGroup` ，

    Notes
    -----

    - 配合 ``tools.map_editor`` 的 bundle / shockwave_field
    - 用 :func:`bind_wave_tracker` / :func:`build_map_view_from_bundle` 装配

    """

    def __init__(
        self,
        bundle: MapBundle,
        dist: np.ndarray | None = None,
        intensity: np.ndarray | None = None,
        wave_radius: float | None = None,
        cell_opacity: float = 0.78,
        show_wave_front: bool = True,
        wave_front_band: float = 0.55,
        ui_font: str = "Sans",
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.bundle = bundle
        self.grid_w = bundle.grid_w
        self.grid_h = bundle.grid_h
        self.dist_field = dist
        self.intensity_field = intensity
        self.wave_radius = wave_radius
        self._cell_opacity = cell_opacity
        self._show_wave_front = show_wave_front
        self._wave_front_band = wave_front_band
        self._ui_font = ui_font

        self.bg = Rectangle(
            width=BUNDLE_MAP_W,
            height=BUNDLE_MAP_H,
            fill_color=BUNDLE_C_BG,
            fill_opacity=1,
            stroke_color=GREY_B,
            stroke_width=2.0,
        )
        self.floor = self._build_floor()
        self.heat, self._heat_cells = self._init_heat_layer()
        self.wave_front, self._front_cells = self._init_wave_front_layer()
        self.overlay = self._build_overlay_markers()
        self.add(self.bg, self.floor, self.heat, self.wave_front, self.overlay)
        self.set_wave_radius(wave_radius)

    def _norm_to_scene(self, nx: float, ny: float) -> np.ndarray:
        return np.array([nx * BUNDLE_MAP_W - BUNDLE_MAP_W / 2, ny * BUNDLE_MAP_H - BUNDLE_MAP_H / 2, 0])

    def _cell_size(self) -> tuple[float, float]:
        return (
            BUNDLE_MAP_W / self.grid_w * (1.0 - BUNDLE_CELL_GAP),
            BUNDLE_MAP_H / self.grid_h * (1.0 - BUNDLE_CELL_GAP),
        )

    def _cell_center_norm(self, i: int, j: int) -> tuple[float, float]:
        return self.bundle.grid_to_norm(i, j)

    def _make_cell_rect(
        self,
        i: int,
        j: int,
        color: str,
        *,
        opacity: float = 1.0,
        stroke_width: float = 0.0,
        stroke_color: str = BUNDLE_C_GLOW,
    ) -> Rectangle:
        cw, ch = self._cell_size()
        rect = Rectangle(
            width=cw,
            height=ch,
            stroke_width=stroke_width,
            stroke_color=stroke_color,
            fill_color=color,
            fill_opacity=opacity,
        )
        rect.move_to(self._norm_to_scene(*self._cell_center_norm(i, j)))
        return rect

    def _floor_color(self, i: int, j: int) -> str:
        r, g, b = (int(v) for v in self.bundle.cell_colors[j, i])
        return rgb_to_hex(r, g, b)

    def _cell_visible(self, i: int, j: int) -> bool:
        if self.bundle.walkable[j, i]:
            return True
        from yty_manim.tools.map_editor.map_bundle import DEFAULT_BG_RGB
        return tuple(int(v) for v in self.bundle.cell_colors[j, i]) != DEFAULT_BG_RGB

    def _build_floor(self) -> VGroup:
        cells = VGroup()
        for j in range(self.grid_h):
            for i in range(self.grid_w):
                if not self._cell_visible(i, j):
                    continue
                rect = self._make_cell_rect(
                    i, j, self._floor_color(i, j),
                    opacity=0.94, stroke_width=0.35, stroke_color=BUNDLE_C_FLOOR_EDGE,
                )
                cells.add(rect)
        return cells

    def _init_heat_layer(self) -> tuple[VGroup, dict[tuple[int, int], Rectangle]]:
        cells = VGroup()
        index: dict[tuple[int, int], Rectangle] = {}
        for j in range(self.grid_h):
            for i in range(self.grid_w):
                if not self.bundle.walkable[j, i]:
                    continue
                rect = self._make_cell_rect(i, j, BUNDLE_C_WALK, opacity=0.0, stroke_width=0.0)
                cells.add(rect)
                index[(i, j)] = rect
        return cells, index

    def _init_wave_front_layer(self) -> tuple[VGroup, dict[tuple[int, int], Rectangle]]:
        cells = VGroup()
        index: dict[tuple[int, int], Rectangle] = {}
        for j in range(self.grid_h):
            for i in range(self.grid_w):
                if not self.bundle.walkable[j, i]:
                    continue
                rect = self._make_cell_rect(
                    i, j, BUNDLE_C_GLOW, opacity=0.0, stroke_width=0.0, stroke_color=BUNDLE_C_GLOW,
                )
                cells.add(rect)
                index[(i, j)] = rect
        return cells, index

    def _hex_to_manim(self, hex_color: str) -> str:
        return hex_color if hex_color.startswith("#") else f"#{hex_color}"

    def _build_overlay_markers(self) -> VGroup:
        grp = VGroup()
        for src in self.bundle.explosion_sources:
            grp.add(self._make_explosion_marker(src))
        for marker in self.bundle.markers:
            grp.add(self._make_text_marker(marker))
        return grp

    def _make_explosion_marker(self, src: ExplosionSource) -> VGroup:
        pos = self._norm_to_scene(*src.norm)
        color = self._hex_to_manim(src.color)
        ring = Circle(radius=0.12, color=color, stroke_width=3.0).move_to(pos)
        dot = Dot(pos, radius=0.065, color=color)
        label = Text(src.label, font=self._ui_font, font_size=14, color=color)
        label.next_to(ring, DOWN, buff=0.05)
        return VGroup(ring, dot, label)

    def _make_text_marker(self, marker: MapMarker) -> VGroup:
        pos = self._norm_to_scene(*marker.norm)
        color = self._hex_to_manim(marker.color)
        ring = Circle(radius=0.09, color=color, stroke_width=2.0).move_to(pos)
        dot = Dot(pos, radius=0.045, color=color)
        parts: list[Mobject] = [ring, dot]
        if marker.label:
            tag = Text(marker.label, font=self._ui_font, font_size=12, color=color)
            tag.next_to(ring, DOWN, buff=0.04)
            parts.append(tag)
        return VGroup(*parts)

    def set_wave_radius(self, radius: float | None) -> None:
        self.wave_radius = radius
        op = self._cell_opacity
        has_field = self.intensity_field is not None and self.dist_field is not None

        for (i, j), rect in self._heat_cells.items():
            if not has_field:
                rect.set_fill(opacity=0.0)
                continue
            d = self.dist_field[j, i]
            if not np.isfinite(d) or (radius is not None and d > radius):
                rect.set_fill(opacity=0.0)
                continue
            t = float(self.intensity_field[j, i])
            if t <= 0:
                rect.set_fill(opacity=0.0)
                continue
            rect.set_fill(intensity_color(t), opacity=op)

        show_front = self._show_wave_front and has_field and radius is not None and radius > 0
        band = self._wave_front_band
        for (i, j), rect in self._front_cells.items():
            if not show_front:
                rect.set_stroke(width=0.0, opacity=0.0)
                continue
            d = self.dist_field[j, i]
            if not np.isfinite(d) or abs(d - radius) > band:
                rect.set_stroke(width=0.0, opacity=0.0)
                continue
            rect.set_stroke(color=BUNDLE_C_GLOW, width=2.4, opacity=0.95)

    def refresh_overlay(self) -> None:
        new_overlay = self._build_overlay_markers()
        self.overlay.become(new_overlay)


def bind_wave_tracker(map_view: GridMapView, wave_t: ValueTracker) -> GridMapView:
    map_view.set_wave_radius(wave_t.get_value())
    map_view.add_updater(lambda m: m.set_wave_radius(wave_t.get_value()))
    return map_view


def build_map_view_from_bundle(
    bundle: MapBundle,
    source_norm: tuple[float, float] | None = None,
    wave_radius: float = 0.0,
    **kwargs,
) -> GridMapView:
    dist, intensity, _ = shockwave_field(bundle, source_norm)
    return GridMapView(
        bundle=bundle,
        dist=dist,
        intensity=intensity,
        wave_radius=wave_radius,
        **kwargs,
    )
