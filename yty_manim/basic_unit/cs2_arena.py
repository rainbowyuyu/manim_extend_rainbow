# rainbow_yu manim_extend.basic_unit.cs2_arena 🐋✨
# CS2 玩具竞技场：三维 Arena + 二维寻路网格

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
import heapq

import numpy as np
from manim import *

from yty_manim.disposition.fonts_and_colors import (
    UI_FONT,
    cs2_arena_3d,
    cs2_pathfinding,
)

__all__ = (
    "GRID",
    "BOMB_IJ",
    "SURVIVOR_IJ",
    "CELL",
    "CELL_2D",
    "FLOOR_H",
    "WALL_H",
    "MAP_SCALE",
    "MAP_SHIFT",
    "Arena3D",
    "GridMap2D",
    "AlgoSpec",
    "FormulaLine",
    "DeepDive",
    "bfs_path",
    "bfs_dist",
    "intensity_to_hp",
)



# ── 三维竞技场 ──────────────────────────────────────────────





# 调色板 / 布局默认值（见 disposition.fonts_and_colors）
BG = cs2_arena_3d["BG"]
FLOOR = cs2_arena_3d["FLOOR"]
FLOOR_SIDE = cs2_arena_3d["FLOOR_SIDE"]
FLOOR_EDGE = cs2_arena_3d["FLOOR_EDGE"]
WALL = cs2_arena_3d["WALL"]
WALL_SIDE = cs2_arena_3d["WALL_SIDE"]
WALL_TOP = cs2_arena_3d["WALL_TOP"]
ACCENT_OLD = cs2_arena_3d["ACCENT_OLD"]
ACCENT_OLD_GLOW = cs2_arena_3d["ACCENT_OLD_GLOW"]
ACCENT_NEW = cs2_arena_3d["ACCENT_NEW"]
ACCENT_NEW_HOT = cs2_arena_3d["ACCENT_NEW_HOT"]
ACCENT_NEW_MID = cs2_arena_3d["ACCENT_NEW_MID"]
BOMB_GLOW = cs2_arena_3d["BOMB_GLOW"]
SAFE = cs2_arena_3d["SAFE"]
TITLE_C = cs2_arena_3d["TITLE_C"]

# ── Example arena ────────────────────────────────────────────────────────────
# Walkable = 1, wall = 0. Multi-room layout: bomb in west courtyard;
# survivor behind a thick L-wall so Euclidean ≪ path distance.
# Path must go south corridor → east → north into the safe pocket.
GRID = np.array(
    [
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 0],
        [0, 1, 1, 1, 1, 1, 0, 1, 1, 0, 0, 0, 1, 1, 0],
        [0, 1, 1, 1, 1, 1, 0, 1, 1, 0, 1, 1, 1, 1, 0],
        [0, 1, 1, 0, 0, 0, 0, 1, 1, 0, 1, 1, 1, 1, 0],
        [0, 1, 1, 0, 1, 1, 1, 1, 1, 0, 1, 1, 0, 0, 0],
        [0, 1, 1, 0, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 0],
        [0, 1, 1, 0, 1, 0, 0, 0, 0, 0, 1, 1, 1, 1, 0],
        [0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0],
        [0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    ],
    dtype=bool,
)
BOMB_IJ = (2, 2)        # west courtyard
SURVIVOR_IJ = (3, 11)   # east pocket behind L-wall (short Euclidean, long path)
CELL = cs2_arena_3d["CELL"]
WALL_H = cs2_arena_3d["WALL_H"]
FLOOR_H = cs2_arena_3d["FLOOR_H"]
TILE_SCALE = cs2_arena_3d["TILE_SCALE"]
WALL_SCALE = cs2_arena_3d["WALL_SCALE"]


def _cell_to_xyz(i: int, j: int, z: float = 0.0) -> np.ndarray:
    rows, cols = GRID.shape
    x = (j - (cols - 1) / 2) * CELL
    y = ((rows - 1) / 2 - i) * CELL
    return np.array([x, y, z], dtype=float)


def _bfs_dist(start: tuple[int, int]) -> np.ndarray:
    h, w = GRID.shape
    dist = np.full((h, w), np.inf)
    si, sj = start
    if not GRID[si, sj]:
        return dist
    dist[si, sj] = 0.0
    q = deque([(si, sj)])
    while q:
        i, j = q.popleft()
        for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            ni, nj = i + di, j + dj
            if 0 <= ni < h and 0 <= nj < w and GRID[ni, nj] and dist[ni, nj] == np.inf:
                dist[ni, nj] = dist[i, j] + 1.0
                q.append((ni, nj))
    return dist


def _bfs_path(start: tuple[int, int], goal: tuple[int, int]) -> list[tuple[int, int]]:
    """Return shortest 4-connected path (list of cells) or []."""
    h, w = GRID.shape
    parent: dict[tuple[int, int], tuple[int, int] | None] = {start: None}
    q = deque([start])
    while q:
        i, j = q.popleft()
        if (i, j) == goal:
            break
        for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            ni, nj = i + di, j + dj
            if 0 <= ni < h and 0 <= nj < w and GRID[ni, nj] and (ni, nj) not in parent:
                parent[(ni, nj)] = (i, j)
                q.append((ni, nj))
    if goal not in parent:
        return []
    path = []
    cur: tuple[int, int] | None = goal
    while cur is not None:
        path.append(cur)
        cur = parent[cur]
    path.reverse()
    return path


def _intensity_from_dist(dist: np.ndarray, max_r: float) -> np.ndarray:
    inten = np.clip(1.0 - dist / max_r, 0.0, 1.0)
    inten[~np.isfinite(dist)] = 0.0
    return inten


def _damage_color(t: float) -> ManimColor:
    """Damage heat: 1→hot red, mid→orange/amber, low→cool teal."""
    t = float(np.clip(t, 0, 1))
    if t >= 0.66:
        u = (t - 0.66) / 0.34
        return interpolate_color(ManimColor("#ff8a3d"), ManimColor("#ff2d2d"), u)
    if t >= 0.33:
        u = (t - 0.33) / 0.33
        return interpolate_color(ManimColor("#f0c040"), ManimColor("#ff8a3d"), u)
    if t > 0.02:
        u = t / 0.33
        return interpolate_color(ManimColor("#3de0c8"), ManimColor("#f0c040"), u)
    return ManimColor(FLOOR)


def intensity_to_hp(t: float) -> int:
    return int(round(120 * float(np.clip(t, 0, 1))))


def _flat_face(
    width: float,
    height: float,
    color: str,
    *,
    center: np.ndarray,
    normal_axis: str,
) -> Rectangle:
    """Single opaque rectangle. width/height are the two in-plane axes after orientation.

    normal +Z: width→X, height→Y
    normal +X: width→Y, height→Z
    normal +Y: width→X, height→Z
    """
    if normal_axis == "z":
        face = Rectangle(width=width, height=height)
    elif normal_axis == "x":
        # After rot about UP: local X→Z, local Y→Y ⇒ pass (height=Z, width=Y) swapped into ctor
        face = Rectangle(width=height, height=width)
        face.rotate(PI / 2, axis=UP)
    elif normal_axis == "y":
        face = Rectangle(width=width, height=height)
        face.rotate(PI / 2, axis=RIGHT)
    else:
        raise ValueError(normal_axis)
    face.set_fill(ManimColor(color), opacity=1)
    face.set_stroke(width=0)
    face.set_shade_in_3d(False)
    face.move_to(center)
    return face


def _wall_box(cx: float, cy: float, sx: float, sy: float, sz: float) -> VGroup:
    """Closed wall as 5 faces (skip bottom). Avoids Cube face dropouts under Cairo."""
    zm = 0.5 * sz
    return VGroup(
        _flat_face(sx, sy, WALL_TOP, center=np.array([cx, cy, sz]), normal_axis="z"),
        _flat_face(sy, sz, WALL_SIDE, center=np.array([cx + sx * 0.5, cy, zm]), normal_axis="x"),
        _flat_face(sy, sz, WALL, center=np.array([cx - sx * 0.5, cy, zm]), normal_axis="x"),
        _flat_face(sx, sz, WALL_SIDE, center=np.array([cx, cy + sy * 0.5, zm]), normal_axis="y"),
        _flat_face(sx, sz, WALL, center=np.array([cx, cy - sy * 0.5, zm]), normal_axis="y"),
    )


def _merged_wall_rects(grid: np.ndarray) -> list[tuple[int, int, int, int]]:
    """Greedy merge of wall cells (grid False) into axis-aligned rectangles (i0,j0,i1,j1)."""
    h, w = grid.shape
    visited = np.zeros((h, w), dtype=bool)
    rects: list[tuple[int, int, int, int]] = []
    for i in range(h):
        for j in range(w):
            if grid[i, j] or visited[i, j]:
                continue
            j1 = j
            while j1 + 1 < w and (not grid[i, j1 + 1]) and (not visited[i, j1 + 1]):
                j1 += 1
            i1 = i
            while i1 + 1 < h:
                row_ok = all(
                    (not grid[i1 + 1, jj]) and (not visited[i1 + 1, jj])
                    for jj in range(j, j1 + 1)
                )
                if not row_ok:
                    break
                i1 += 1
            for ii in range(i, i1 + 1):
                visited[ii, j : j1 + 1] = True
            rects.append((i, j, i1, j1))
    return rects


def _set_tile_color(tile: Mobject, color: ManimColor | str) -> None:
    """Recolor a floor tile (Square or VGroup), keeping shade off."""
    c = ManimColor(color)
    tile.set_shade_in_3d(False)
    tile.set_stroke(width=0)
    tile.set_fill(c, opacity=1)
    for sub in tile.submobjects:
        sub.set_shade_in_3d(False)
        sub.set_stroke(width=0)
        sub.set_fill(c, opacity=1)


# ── Shared 3D arena ──────────────────────────────────────────────────────────
class Arena3D(VGroup):
    """
    CS2 C4 风格三维竞技场，
    继承于 :class:`~.VGroup` ，

    Notes
    -----

    - 基于共享 ``GRID`` 玩具地图：地板片 + 合并墙体 + 炸弹/幸存者标记
    - 常与冲击波 / 球体爆炸对比场景一起使用

    Examples
    --------

    >>> class ArenaDemo(ThreeDScene):
    >>>     def construct(self):
    >>>         self.add(Arena3D())
    >>>         self.wait()

    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.floor_cells: dict[tuple[int, int], Mobject] = {}
        self.wall_blocks: list[VGroup] = []
        rows, cols = GRID.shape

        plate = Prism(dimensions=[cols * CELL + 0.5, rows * CELL + 0.5, 0.05])
        plate.set_fill(ManimColor("#121822"), opacity=1).set_stroke(width=0)
        plate.set_shade_in_3d(False)
        plate.move_to([0, 0, -0.04])
        self.add(plate)

        # Floors: single XY square each (no multi-face Cube → no missing slabs)
        for i in range(rows):
            for j in range(cols):
                if not GRID[i, j]:
                    continue
                c = _cell_to_xyz(i, j)
                tile = _flat_face(
                    CELL * TILE_SCALE,
                    CELL * TILE_SCALE,
                    FLOOR,
                    center=np.array([c[0], c[1], FLOOR_H]),
                    normal_axis="z",
                )
                self.floor_cells[(i, j)] = tile
                self.add(tile)

        # Walls: merge contiguous cells into continuous boxes (no gaps / missing mid faces)
        for i0, j0, i1, j1 in _merged_wall_rects(GRID):
            c0 = _cell_to_xyz(i0, j0)
            c1 = _cell_to_xyz(i1, j1)
            cx = 0.5 * (c0[0] + c1[0])
            cy = 0.5 * (c0[1] + c1[1])
            sx = (j1 - j0 + 1) * CELL * 0.98
            sy = (i1 - i0 + 1) * CELL * 0.98
            wall = _wall_box(cx, cy, sx, sy, WALL_H)
            self.wall_blocks.append(wall)
            self.add(wall)

        bc = _cell_to_xyz(*BOMB_IJ, z=FLOOR_H + 0.26)
        self.bomb = Sphere(radius=0.16, resolution=(12, 12))
        self.bomb.set_fill(ManimColor(BOMB_GLOW), opacity=1).set_stroke(width=0)
        self.bomb.set_shade_in_3d(False)
        self.bomb.move_to(bc)
        ring = Circle(radius=0.28, color=ManimColor(BOMB_GLOW), stroke_width=2.5)
        ring.move_to([bc[0], bc[1], FLOOR_H + 0.02])
        self.bomb_group = VGroup(self.bomb, ring)
        self.add(self.bomb_group)

        sc = _cell_to_xyz(*SURVIVOR_IJ, z=FLOOR_H + 0.32)
        body = Sphere(radius=0.14, resolution=(10, 10))
        body.set_fill(ManimColor(SAFE), opacity=1).set_stroke(width=0)
        body.set_shade_in_3d(False)
        body.stretch_to_fit_depth(0.5)
        body.move_to(sc)
        head = Sphere(radius=0.1, resolution=(8, 8))
        head.set_fill(ManimColor("#a7f3d0"), opacity=1).set_stroke(width=0)
        head.set_shade_in_3d(False)
        head.move_to(sc + OUT * 0.38)
        self.survivor = VGroup(body, head)
        self.add(self.survivor)


def _hud_title(text: str, subtitle: str, accent: str) -> VGroup:
    t = Text(text, font=UI_FONT, font_size=34, color=ManimColor(TITLE_C))
    s = Text(subtitle, font=UI_FONT, font_size=18, color=ManimColor(accent))
    return VGroup(t, s).arrange(DOWN, buff=0.1)


def _wire_sphere(radius: float, color: ManimColor, center: np.ndarray, n_lat: int = 10, n_lon: int = 12) -> VGroup:
    """Wireframe-only sphere (no fill) — avoids Cairo depth-sort vanishing cubes."""
    g = VGroup()
    # Latitude rings (horizontal)
    for k in range(1, n_lat):
        phi = PI * k / n_lat
        r_ring = radius * np.sin(phi)
        z = radius * np.cos(phi)
        if r_ring < 1e-3:
            continue
        ring = Circle(radius=r_ring, color=color, stroke_width=1.4)
        ring.move_to(center + OUT * z)
        g.add(ring)
    # Longitude arcs approximated as Circles in vertical planes
    for k in range(n_lon):
        theta = TAU * k / n_lon
        circ = Circle(radius=radius, color=color, stroke_width=1.1)
        circ.rotate(PI / 2, axis=RIGHT)
        circ.rotate(theta, axis=OUT)
        circ.move_to(center)
        g.add(circ)
    for m in g:
        m.set_stroke(color=color, width=1.2, opacity=0.9)
    return g


bfs_path = _bfs_path
bfs_dist = _bfs_dist

# ── 二维寻路网格 ────────────────────────────────────────────




MAP_SHIFT = LEFT * cs2_pathfinding["MAP_SHIFT_LEFT"] + UP * cs2_pathfinding["MAP_SHIFT_UP"]
MAP_SCALE = cs2_pathfinding["MAP_SCALE"]
PANEL_BUFF = cs2_pathfinding["PANEL_BUFF"]
Z_MAP = cs2_pathfinding["Z_MAP"]
Z_PANEL = cs2_pathfinding["Z_PANEL"]
Z_METRICS = cs2_pathfinding["Z_METRICS"]
Z_PATH = cs2_pathfinding["Z_PATH"]
Z_MARKERS = cs2_pathfinding["Z_MARKERS"]


def _apply_layer_order(scene: Scene, map_body, panel, metrics_layer, path_group, markers) -> None:
    map_body.set_z_index(Z_MAP)
    panel.set_z_index(Z_PANEL)
    metrics_layer.set_z_index(Z_METRICS)
    path_group.set_z_index(Z_PATH)
    markers.set_z_index(Z_MARKERS)
    scene.bring_to_front(map_body, panel, metrics_layer, path_group, markers)


def _place_formula_panel(panel: VGroup, map_body: Mobject) -> VGroup:
    """侧栏贴地图右侧；趣味卡在文字面板下方居中（不在面板内）。"""
    panel.next_to(map_body, RIGHT, buff=PANEL_BUFF)
    panel.align_to(map_body, UP).shift(DOWN * 0.18)
    if len(panel) >= 3:
        rect, fun = panel[0], panel[2]
        fun.next_to(rect, DOWN, buff=0.38)
        fun.set_x(rect.get_center()[0])
    return panel


# ── Palette ────────────────────────────────────────────────────────────────────
C_BG = cs2_pathfinding["C_BG"]
C_FLOOR = cs2_pathfinding["C_FLOOR"]
C_WALL = cs2_pathfinding["C_WALL"]
C_WALL_EDGE = cs2_pathfinding["C_WALL_EDGE"]
C_START = cs2_pathfinding["C_START"]
C_GOAL = cs2_pathfinding["C_GOAL"]
C_PATH = cs2_pathfinding["C_PATH"]
C_PANEL = cs2_pathfinding["C_PANEL"]
C_PANEL_EDGE = cs2_pathfinding["C_PANEL_EDGE"]
C_TITLE = cs2_pathfinding["C_TITLE"]
C_SUB = cs2_pathfinding["C_SUB"]
C_VIS_COOL = cs2_pathfinding["C_VIS_COOL"]
C_VIS_MID = cs2_pathfinding["C_VIS_MID"]
C_VIS_HOT = cs2_pathfinding["C_VIS_HOT"]
C_EUCL = cs2_pathfinding["C_EUCL"]

CELL_2D = cs2_pathfinding["CELL_2D"]
CELL_GAP = cs2_pathfinding["CELL_GAP"]



def _ij_to_xy(i: int, j: int) -> np.ndarray:
    rows, cols = GRID.shape
    x = (j - (cols - 1) / 2) * CELL_2D
    y = ((rows - 1) / 2 - i) * CELL_2D
    return np.array([x, y, 0.0])


def _walkable_cells() -> list[tuple[int, int]]:
    return [(i, j) for i in range(GRID.shape[0]) for j in range(GRID.shape[1]) if GRID[i, j]]


def _neighbors4(i: int, j: int) -> list[tuple[int, int, float]]:
    out = []
    for di, dj, w in ((1, 0, 1.0), (-1, 0, 1.0), (0, 1, 1.0), (0, -1, 1.0)):
        ni, nj = i + di, j + dj
        if 0 <= ni < GRID.shape[0] and 0 <= nj < GRID.shape[1] and GRID[ni, nj]:
            out.append((ni, nj, w))
    return out


def _neighbors8(i: int, j: int) -> list[tuple[int, int, float]]:
    out = []
    for di in (-1, 0, 1):
        for dj in (-1, 0, 1):
            if di == 0 and dj == 0:
                continue
            ni, nj = i + di, j + dj
            if 0 <= ni < GRID.shape[0] and 0 <= nj < GRID.shape[1] and GRID[ni, nj]:
                w = 1.414 if di and dj else 1.0
                out.append((ni, nj, w))
    return out


def _reconstruct(parent: dict[tuple[int, int], tuple[int, int] | None], goal: tuple[int, int]) -> list[tuple[int, int]]:
    if goal not in parent:
        return []
    path = []
    cur: tuple[int, int] | None = goal
    while cur is not None:
        path.append(cur)
        cur = parent[cur]
    path.reverse()
    return path


def _heat_color(t: float) -> ManimColor:
    t = float(np.clip(t, 0, 1))
    if t < 0.45:
        return interpolate_color(ManimColor(C_VIS_COOL), ManimColor(C_VIS_MID), t / 0.45)
    return interpolate_color(ManimColor(C_VIS_MID), ManimColor(C_VIS_HOT), (t - 0.45) / 0.55)


def _layers_from_dist(dist: np.ndarray) -> list[list[tuple[int, int]]]:
    finite = [(dist[i, j], i, j) for i, j in _walkable_cells() if np.isfinite(dist[i, j])]
    if not finite:
        return []
    finite.sort(key=lambda x: x[0])
    layers: list[list[tuple[int, int]]] = []
    cur_key = None
    bucket: list[tuple[int, int]] = []
    for d, i, j in finite:
        key = int(np.floor(d + 1e-6))
        if cur_key is None:
            cur_key = key
        if key != cur_key:
            layers.append(bucket)
            bucket = []
            cur_key = key
        bucket.append((i, j))
    if bucket:
        layers.append(bucket)
    return layers


@dataclass
class FormulaLine:
    """math: MathTex source (when LaTeX available); display: always-readable formula text."""

    math: str
    display: str
    caption: str = ""


@dataclass
class DeepDive:
    """算法演示后的精讲卡片。"""

    headline: str
    steps: list[tuple[str, str]]  # (短标题, 说明)
    insight: str
    formula_focus: str  # 主公式 ASCII


def _deep_dive_for(key: str) -> DeepDive:
    table = {
        "euclid": DeepDive(
            headline="欧氏 · 计算方式",
            steps=[
                ("取直线", "只算起点到点的直线长度，墙不参与"),
                ("半径截断", "超过爆炸半径 R 的点强度为 0"),
                ("映射伤害", "I = max(0, 1 - d/R)，距离越近伤越高"),
            ],
            insight="结论：拐角「看起来近」也会满伤 — 这就是旧机制的问题",
            formula_focus="d = ||p - s||_2",
        ),
        "bfs": DeepDive(
            headline="BFS · 计算方式",
            steps=[
                ("队列扩展", "FIFO：先到的格子先扩展邻居"),
                ("单位代价", "每走一格 +1，得到最少步数"),
                ("波前同步", "同一层格子同时点亮，像涟漪"),
            ],
            insight="CS2 烘焙的直觉原型：离散冲击波一层层铺开",
            formula_focus="d(v) = d(u) + 1",
        ),
        "dijkstra": DeepDive(
            headline="Dijkstra · 计算方式",
            steps=[
                ("优先队列", "永远先处理当前累计代价最小的点"),
                ("松弛更新", "若经 u 到 v 更短，就改写 d(v)"),
                ("对角权重", "直走代价 1，斜走约 sqrt(2)"),
            ],
            insight="编译期烘焙距离场：精确、可复用、运行时只查表",
            formula_focus="d(v) = min(d(u) + w(u,v))",
        ),
        "astar": DeepDive(
            headline="A* · 计算方式",
            steps=[
                ("双代价", "g = 已走路程，h = 估计到终点"),
                ("排序键", "每次扩展 f = g + h 最小的节点"),
                ("可采纳 h", "h 不低估真距离时，结果仍最优"),
            ],
            insight="比 Dijkstra 少探索，却仍能保证最短路 — 运行时寻路首选",
            formula_focus="f(n) = g(n) + h(n)",
        ),
        "manhattan": DeepDive(
            headline="曼哈顿 · 计算方式",
            steps=[
                ("直角折线", "h = |dx| + |dy|，只计横竖"),
                ("启发用途", "常作为 A* / 贪心的 h(n)"),
                ("可采纳性", "四连通下 h <= 真最短路"),
            ],
            insight="本身不是搜路，而是给搜索「方向感」的尺子",
            formula_focus="h = |xn-xg| + |yn-yg|",
        ),
        "greedy": DeepDive(
            headline="贪心 · 计算方式",
            steps=[
                ("只看 h", "扩展时忽略已走代价 g"),
                ("冲向终点", "谁离终点「看起来」近就先走谁"),
                ("可能绕远", "快，但不保证全局最短"),
            ],
            insight="对照 A*：少了 g，就丢了「已经花了多少」的记忆",
            formula_focus="f(n) = h(n)",
        ),
    }
    return table[key]


@dataclass
class AlgoSpec:
    key: str
    title: str
    subtitle: str
    formulas: list[FormulaLine]
    note: str
    accent: str
    layers: list[list[tuple[int, int]]]
    dist: np.ndarray
    path: list[tuple[int, int]]
    ring_mode: bool = False
    max_ring: float = 0.0
    cell_metrics: dict[tuple[int, int], str] = field(default_factory=dict)


def _field_inf() -> np.ndarray:
    return np.full(GRID.shape, np.inf)


def _algo_euclidean(start: tuple[int, int]) -> AlgoSpec:
    dist = _field_inf()
    si, sj = start
    sx, sy = _ij_to_xy(si, sj)[:2]
    for i, j in _walkable_cells():
        px, py = _ij_to_xy(i, j)[:2]
        dist[i, j] = float(np.hypot(px - sx, py - sy) / CELL_2D)
    layers = _layers_from_dist(dist)
    return AlgoSpec(
        key="euclid",
        title="欧氏距离场",
        subtitle="旧球体模型 · 无视墙体",
        formulas=[
            FormulaLine(
                r"d(\mathbf{p})=\|\mathbf{p}-\mathbf{s}\|_2",
                "d(p) = ||p - s||_2",
            ),
            FormulaLine(
                r"I(\mathbf{p})=\max\!\left(0,\,1-\dfrac{d}{R}\right)",
                "I(p) = max(0, 1 - d/R)",
            ),
        ],
        note="直线距离穿墙，拐角与开阔区同伤",
        accent=C_EUCL,
        layers=layers,
        dist=dist,
        path=[],
        ring_mode=True,
        max_ring=float(np.nanmax(dist[np.isfinite(dist)])) + 0.5,
    )


def _algo_bfs(start: tuple[int, int], goal: tuple[int, int]) -> AlgoSpec:
    dist = _field_inf()
    parent: dict[tuple[int, int], tuple[int, int] | None] = {start: None}
    dist[start[0], start[1]] = 0.0
    q = deque([start])
    order: list[tuple[int, int]] = []
    while q:
        cell = q.popleft()
        order.append(cell)
        for ni, nj, _ in _neighbors4(*cell):
            if np.isfinite(dist[ni, nj]):
                continue
            dist[ni, nj] = dist[cell[0], cell[1]] + 1.0
            parent[(ni, nj)] = cell
            q.append((ni, nj))
    layers = []
    cur = 0
    bucket: list[tuple[int, int]] = []
    for i, j in order:
        d = int(dist[i, j])
        if d != cur:
            if bucket:
                layers.append(bucket)
            bucket = []
            cur = d
        bucket.append((i, j))
    if bucket:
        layers.append(bucket)
    return AlgoSpec(
        key="bfs",
        title="广度优先搜索 BFS",
        subtitle="单位步长 · 最少格子数",
        formulas=[
            FormulaLine(r"d(v)=d(u)+1", "d(v) = d(u) + 1", "四连通网格"),
            FormulaLine(r"O(|V|+|E|)", "O(|V| + |E|)", "队列 FIFO"),
        ],
        note="CS2 烘焙的离散波前：一层层向外扩展",
        accent=C_VIS_COOL,
        layers=layers,
        dist=dist,
        path=_reconstruct(parent, goal),
    )


def _algo_dijkstra(start: tuple[int, int], goal: tuple[int, int]) -> AlgoSpec:
    dist = _field_inf()
    parent: dict[tuple[int, int], tuple[int, int] | None] = {start: None}
    dist[start[0], start[1]] = 0.0
    pq: list[tuple[float, int, int]] = [(0.0, start[0], start[1])]
    order: list[tuple[int, int]] = []
    metrics: dict[tuple[int, int], str] = {}
    while pq:
        d, i, j = heapq.heappop(pq)
        if d > dist[i, j]:
            continue
        order.append((i, j))
        metrics[(i, j)] = f"{d:.1f}"
        for ni, nj, w in _neighbors8(i, j):
            nd = d + w
            if nd < dist[ni, nj]:
                dist[ni, nj] = nd
                parent[(ni, nj)] = (i, j)
                heapq.heappush(pq, (nd, ni, nj))
    layers = []
    for k in range(0, len(order), 3):
        layers.append(order[k : k + 3])
    return AlgoSpec(
        key="dijkstra",
        title="Dijkstra 最短路",
        subtitle="带权图 · 八连通对角步",
        formulas=[
            FormulaLine(
                r"d(v)=\min\!\bigl(d(u)+w(u,v)\bigr)",
                "d(v) = min(d(u) + w(u,v))",
            ),
            FormulaLine(r"w\in\{1,\ \sqrt{2}\,\}", "w in {1, sqrt(2)}"),
        ],
        note="编译期烘焙距离场：精确累计路径代价",
        accent=C_VIS_MID,
        layers=layers,
        dist=dist,
        path=_reconstruct(parent, goal),
        cell_metrics=metrics,
    )


def _heuristic(i: int, j: int, goal: tuple[int, int], kind: str) -> float:
    gi, gj = goal
    di, dj = abs(i - gi), abs(j - gj)
    if kind == "manhattan":
        return float(di + dj)
    if kind == "chebyshev":
        return float(max(di, dj))
    return float(np.hypot(di, dj))


def _algo_astar(start: tuple[int, int], goal: tuple[int, int]) -> AlgoSpec:
    g = _field_inf()
    parent: dict[tuple[int, int], tuple[int, int] | None] = {start: None}
    g[start[0], start[1]] = 0.0
    h0 = _heuristic(*start, goal, "euclidean")
    pq: list[tuple[float, float, int, int]] = [(h0, 0.0, start[0], start[1])]
    closed: set[tuple[int, int]] = set()
    order: list[tuple[int, int]] = []
    metrics: dict[tuple[int, int], str] = {}
    metrics[start] = f"{h0:.1f}"
    while pq:
        f, gd, i, j = heapq.heappop(pq)
        if (i, j) in closed:
            continue
        closed.add((i, j))
        order.append((i, j))
        metrics[(i, j)] = f"{f:.1f}"
        if (i, j) == goal:
            break
        for ni, nj, w in _neighbors8(i, j):
            if (ni, nj) in closed:
                continue
            ng = gd + w
            if ng < g[ni, nj]:
                g[ni, nj] = ng
                parent[(ni, nj)] = (i, j)
                nh = _heuristic(ni, nj, goal, "euclidean")
                nf = ng + nh
                heapq.heappush(pq, (nf, ng, ni, nj))
    layers = []
    for k in range(0, len(order), 2):
        layers.append(order[k : k + 2])
    return AlgoSpec(
        key="astar",
        title="A* 搜索",
        subtitle="启发式引导 · 目标导向",
        formulas=[
            FormulaLine(r"f(n)=g(n)+h(n)", "f(n) = g(n) + h(n)"),
            FormulaLine(r"h(n)=\|n-g\|_2", "h(n) = ||n - g||_2"),
        ],
        note="优先扩展 f 最小节点，通常比 Dijkstra 更少探索",
        accent="#a78bfa",
        layers=layers,
        dist=g,
        path=_reconstruct(parent, goal),
        cell_metrics=metrics,
    )


def _algo_greedy(start: tuple[int, int], goal: tuple[int, int]) -> AlgoSpec:
    parent: dict[tuple[int, int], tuple[int, int] | None] = {start: None}
    h0 = _heuristic(*start, goal, "euclidean")
    pq: list[tuple[float, int, int]] = [(h0, start[0], start[1])]
    visited: set[tuple[int, int]] = set()
    order: list[tuple[int, int]] = []
    dist = _field_inf()
    dist[start[0], start[1]] = 0.0
    metrics: dict[tuple[int, int], str] = {start: f"{h0:.1f}"}
    while pq:
        h_pop, i, j = heapq.heappop(pq)
        if (i, j) in visited:
            continue
        visited.add((i, j))
        order.append((i, j))
        h = _heuristic(i, j, goal, "euclidean")
        metrics[(i, j)] = f"{h:.1f}"
        if (i, j) == goal:
            break
        for ni, nj, w in _neighbors8(i, j):
            if (ni, nj) in visited:
                continue
            if not np.isfinite(dist[ni, nj]):
                dist[ni, nj] = dist[i, j] + w
                parent[(ni, nj)] = (i, j)
                nh = _heuristic(ni, nj, goal, "euclidean")
                heapq.heappush(pq, (nh, ni, nj))
    layers = []
    for k in range(0, len(order), 2):
        layers.append(order[k : k + 2])
    return AlgoSpec(
        key="greedy",
        title="贪心最佳优先",
        subtitle="仅看启发式 h(n)",
        formulas=[
            FormulaLine(r"f(n)=h(n)", "f(n) = h(n)", "忽略已走代价 g"),
            FormulaLine(r"h=|x|+|y|", "h = |x| + |y|", "或欧氏 ||n-g||"),
        ],
        note="快但不保证最优；对比 A* 理解 g 的作用",
        accent="#fb923c",
        layers=layers,
        dist=dist,
        path=_reconstruct(parent, goal),
        cell_metrics=metrics,
    )


def _algo_manhattan_field(start: tuple[int, int], goal: tuple[int, int]) -> AlgoSpec:
    dist = _field_inf()
    for i, j in _walkable_cells():
        dist[i, j] = _heuristic(i, j, goal, "manhattan")
    layers = _layers_from_dist(dist)
    return AlgoSpec(
        key="manhattan",
        title="曼哈顿启发场",
        subtitle="网格 L1 距离 · 常用 h(n)",
        formulas=[
            FormulaLine(r"h(n)=|x_n-x_g|+|y_n-y_g|", "h(n) = |xn - xg| + |yn - yg|"),
            FormulaLine(r"h\le h^*", "h <= h*  =>  A*", "可采纳启发，结果仍最优"),
        ],
        note="直角折线距离，适合四连通网格启发",
        accent="#38bdf8",
        layers=layers,
        dist=dist,
        path=[],
        ring_mode=True,
        max_ring=float(np.nanmax(dist[np.isfinite(dist)])) + 0.5,
    )


# ── 2D map view ──────────────────────────────────────────────────────────────
class GridMap2D(VGroup):
    """
    二维网格地图与寻路可视化，
    继承于 :class:`~.VGroup` ，

    Notes
    -----

    - 与 :class:`Arena3D` 共用 ``GRID`` / ``BOMB_IJ`` / ``SURVIVOR_IJ``
    - 支持按层刷色、路径折线、起终点标记

    Examples
    --------

    >>> class GridDemo(Scene):
    >>>     def construct(self):
    >>>         m = GridMap2D(BOMB_IJ, SURVIVOR_IJ)
    >>>         self.add(m)

    """
    def __init__(self, start: tuple[int, int], goal: tuple[int, int]):
        super().__init__()
        self.start = start
        self.goal = goal
        self.tiles: dict[tuple[int, int], RoundedRectangle] = {}
        self.markers = VGroup()
        rows, cols = GRID.shape
        cw = CELL_2D * (1 - CELL_GAP)
        ch = CELL_2D * (1 - CELL_GAP)

        border = RoundedRectangle(
            width=cols * CELL_2D + 0.35,
            height=rows * CELL_2D + 0.35,
            corner_radius=0.12,
            stroke_color=C_PANEL_EDGE,
            stroke_width=1.5,
            fill_color=C_PANEL,
            fill_opacity=0.35,
        )
        self.add(border)

        for i in range(rows):
            for j in range(cols):
                pos = _ij_to_xy(i, j)
                if GRID[i, j]:
                    tile = RoundedRectangle(
                        width=cw,
                        height=ch,
                        corner_radius=0.06,
                        fill_color=C_FLOOR,
                        fill_opacity=1,
                        stroke_width=0.8,
                        stroke_color="#2a3a50",
                        stroke_opacity=0.5,
                    )
                    tile.move_to(pos)
                    self.tiles[(i, j)] = tile
                    self.add(tile)
                else:
                    wall = RoundedRectangle(
                        width=cw * 1.02,
                        height=ch * 1.02,
                        corner_radius=0.05,
                        fill_color=C_WALL,
                        fill_opacity=1,
                        stroke_width=0.6,
                        stroke_color=C_WALL_EDGE,
                        stroke_opacity=0.55,
                    )
                    wall.move_to(pos)
                    self.add(wall)

        self._highlight_endpoint_tile(start, C_START)
        self._highlight_endpoint_tile(goal, C_GOAL)
        self._add_marker(start, C_START, "起点")
        self._add_marker(goal, C_GOAL, "终点")

    def apply_map_transform(self, scale: float, shift: np.ndarray) -> None:
        self.scale(scale).shift(shift)
        self.markers.scale(scale).shift(shift)

    def _highlight_endpoint_tile(self, ij: tuple[int, int], color: str) -> None:
        if ij not in self.tiles:
            return
        self.tiles[ij].set_stroke(ManimColor(color), width=2.8, opacity=1.0)
        self.tiles[ij].set_fill(
            interpolate_color(ManimColor(C_FLOOR), ManimColor(color), 0.35),
            opacity=1,
        )

    def _add_marker(self, ij: tuple[int, int], color: str, label: str) -> None:
        pos = _ij_to_xy(*ij)
        ring = Circle(radius=CELL_2D * 0.44, color=ManimColor(color), stroke_width=3.5)
        ring.set_fill(ManimColor(color), opacity=0.18)
        ring.move_to(pos)
        dot = Dot(pos, radius=0.13, color=ManimColor(color))
        dot.set_stroke(WHITE, width=1.5, opacity=0.9)
        tag_bg = RoundedRectangle(
            width=0.62,
            height=0.28,
            corner_radius=0.06,
            fill_color=ManimColor(color),
            fill_opacity=0.92,
            stroke_width=0,
        )
        tag_bg.move_to(pos + UP * 0.42)
        tag = Text(label, font=UI_FONT, font_size=15, color=BLACK, weight=BOLD)
        tag.move_to(tag_bg)
        for m in (ring, dot, tag_bg, tag):
            m.set_z_index(Z_MARKERS)
        self.markers.add(ring, dot, tag_bg, tag)

    def reset_tiles(self) -> None:
        for tile in self.tiles.values():
            tile.set_fill(ManimColor(C_FLOOR), opacity=1)
            tile.set_stroke(color="#2a3a50", width=0.8, opacity=0.5)
        self._highlight_endpoint_tile(self.start, C_START)
        self._highlight_endpoint_tile(self.goal, C_GOAL)

    def make_metric_label(self, ij: tuple[int, int], text: str) -> Text | None:
        if ij not in self.tiles:
            return None
        tile = self.tiles[ij]
        lbl = Text(
            text,
            font="Consolas",
            font_size=11,
            color=WHITE,
            weight=BOLD,
        )
        max_w = CELL_2D * (1 - CELL_GAP) * 0.92 * MAP_SCALE
        if lbl.width > max_w:
            lbl.scale_to_fit_width(max_w)
        lbl.move_to(tile.get_center())
        lbl.set_z_index(Z_METRICS)
        return lbl


def _math_formula(line: FormulaLine) -> Mobject:
    """ASCII → Consolas；含中文则用 UI 字体，避免白框。"""
    if any(ord(ch) > 127 for ch in line.display):
        return Text(line.display, font=UI_FONT, font_size=20, color=WHITE)
    return Text(line.display, font="Consolas", font_size=22, color=WHITE)


def _panel_corner_art(spec: AlgoSpec) -> VGroup:
    """右侧面板右下角：小示意 + 一句趣味点，填补留白。"""
    accent = ManimColor(spec.accent)
    art = VGroup()
    tip = ""

    if spec.key == "euclid":
        tip = "墙挡不住直线"
        wall = Line(UP * 0.28, DOWN * 0.28, stroke_color="#6a7588", stroke_width=3.5)
        ring = Circle(radius=0.42, stroke_color=accent, stroke_width=1.8).set_fill(opacity=0)
        s = Dot(LEFT * 0.28, radius=0.05, color=C_START)
        g = Dot(RIGHT * 0.28, radius=0.05, color=C_GOAL)
        dash = DashedLine(s.get_center(), g.get_center(), stroke_color=accent, stroke_width=1.2, dash_length=0.08)
        dash.set_opacity(0.7)
        art = VGroup(wall, ring, dash, s, g)
    elif spec.key == "bfs":
        tip = "同层同时点亮"
        s = Dot(ORIGIN, radius=0.045, color=C_START)
        rings = VGroup(
            *[
                Square(side_length=0.28 + 0.22 * k, stroke_color=accent, stroke_width=1.4, stroke_opacity=0.4 + 0.2 * k)
                .set_fill(opacity=0)
                for k in range(3)
            ]
        )
        art = VGroup(rings, s)
    elif spec.key == "dijkstra":
        tip = "代价越小越优先"
        s = Dot(LEFT * 0.32 + DOWN * 0.12, radius=0.045, color=C_START)
        g = Dot(RIGHT * 0.32 + UP * 0.12, radius=0.045, color=C_GOAL)
        mid = ORIGIN + UP * 0.2
        segs = VGroup(
            Line(s.get_center(), mid, stroke_color=accent, stroke_width=2.0).set_fill(opacity=0),
            Line(mid, g.get_center(), stroke_color=accent, stroke_width=2.0).set_fill(opacity=0),
        )
        tags = VGroup(
            Text("1", font="Consolas", font_size=11, color=C_SUB).next_to(segs[0], LEFT, buff=0.04),
            Text("√2", font="Consolas", font_size=10, color=C_SUB).next_to(segs[1], UP, buff=0.02),
        )
        art = VGroup(segs, tags, s, g)
    elif spec.key == "astar":
        tip = "g 记路程，h 看终点"
        g_lbl = Text("g", font="Consolas", font_size=16, color=C_VIS_MID)
        plus = Text("+", font="Consolas", font_size=16, color=C_SUB)
        h_lbl = Text("h", font="Consolas", font_size=16, color=accent)
        eq = Text("= f", font="Consolas", font_size=16, color=C_TITLE)
        row = VGroup(g_lbl, plus, h_lbl, eq).arrange(RIGHT, buff=0.1)
        brace = Line(row.get_left() + DOWN * 0.18, row.get_right() + DOWN * 0.18, stroke_color=accent, stroke_width=1.5)
        art = VGroup(row, brace)
    elif spec.key == "manhattan":
        tip = "只走横竖，像城市街区"
        diamond = RegularPolygon(4, radius=0.48, stroke_color=accent, stroke_width=1.8).set_fill(opacity=0)
        diamond.rotate(PI / 4)
        axes = VGroup(
            Line(LEFT * 0.5, RIGHT * 0.5, stroke_color=C_SUB, stroke_width=1.0, stroke_opacity=0.5),
            Line(DOWN * 0.5, UP * 0.5, stroke_color=C_SUB, stroke_width=1.0, stroke_opacity=0.5),
        )
        art = VGroup(axes, diamond)
    else:  # greedy
        tip = "只管更近，不管已花"
        s = Dot(LEFT * 0.35, radius=0.045, color=C_START)
        g = Dot(RIGHT * 0.35, radius=0.045, color=C_GOAL)
        shaft = Line(s.get_center() + RIGHT * 0.08, g.get_center() + LEFT * 0.12, stroke_color=accent, stroke_width=2.0)
        shaft.set_fill(opacity=0)
        h = Text("h only", font="Consolas", font_size=12, color=accent).next_to(shaft, UP, buff=0.06)
        art = VGroup(shaft, h, s, g)

    if art.width > 1.55:
        art.scale_to_fit_width(1.55)
    if art.height > 1.05:
        art.scale_to_fit_height(1.05)

    tip_txt = Text(tip, font=UI_FONT, font_size=13, color=C_SUB)
    if tip_txt.width > 1.7:
        tip_txt.set_width(1.7)
    chip = RoundedRectangle(
        width=max(art.width, tip_txt.width) + 0.28,
        height=art.height + tip_txt.height + 0.36,
        corner_radius=0.1,
        fill_color="#121a28",
        fill_opacity=1,
        stroke_color=accent,
        stroke_width=1.2,
        stroke_opacity=0.55,
    )
    block = VGroup(art, tip_txt).arrange(DOWN, buff=0.12)
    block.move_to(chip.get_center())
    return VGroup(chip, block)


def _formula_panel(spec: AlgoSpec) -> VGroup:
    """文字面板仅含标题/公式/说明；趣味信息在面板外下方居中。"""
    pad_x, pad_y = 0.52, 0.42
    title = Text(spec.title, font=UI_FONT, font_size=26, color=ManimColor(C_TITLE))
    sub = Text(spec.subtitle, font=UI_FONT, font_size=16, color=ManimColor(spec.accent))
    header = VGroup(title, sub).arrange(DOWN, buff=0.1, aligned_edge=LEFT)

    formula_blocks = VGroup()
    for line in spec.formulas:
        m = _math_formula(line)
        block = VGroup(m)
        if line.caption:
            cap = Text(line.caption, font=UI_FONT, font_size=14, color=C_SUB)
            block = VGroup(m, cap).arrange(DOWN, buff=0.08, aligned_edge=LEFT)
        formula_blocks.add(block)
    formula_blocks.arrange(DOWN, buff=0.22, aligned_edge=LEFT)

    note = Text(spec.note, font=UI_FONT, font_size=15, color="#c8d4e8", line_spacing=0.9)
    text_stack = VGroup(header, formula_blocks, note).arrange(DOWN, buff=0.28, aligned_edge=LEFT)
    text_w = max(header.width, formula_blocks.width, note.width, 3.6)
    note.set_width(min(note.width, text_w))

    rect = RoundedRectangle(
        width=text_stack.width + 2 * pad_x,
        height=text_stack.height + 2 * pad_y,
        corner_radius=0.16,
        fill_color=C_PANEL,
        fill_opacity=0.94,
        stroke_color=C_PANEL_EDGE,
        stroke_width=1.2,
    )
    text_stack.move_to(rect.get_center())

    fun = _panel_corner_art(spec)
    fun.next_to(rect, DOWN, buff=0.38)
    fun.set_x(rect.get_center()[0])

    # [0]=面板框，[1]=正文，[2]=面板外趣味卡
    return VGroup(rect, text_stack, fun)


def _path_mobject(path: list[tuple[int, int]], color: str = C_PATH, scale: float = MAP_SCALE, shift: np.ndarray = MAP_SHIFT) -> VMobject:
    if len(path) < 2:
        return VGroup()
    pts = [_ij_to_xy(i, j) for i, j in path]
    line = VMobject()
    line.set_points_as_corners(pts)
    line.set_stroke(ManimColor(color), width=6, opacity=0.95)
    glow = line.copy().set_stroke(ManimColor(color), width=12, opacity=0.22)
    grp = VGroup(glow, line)
    grp.scale(scale).shift(shift)
    grp.set_z_index(Z_PATH)
    return grp

# 兼容：二维格子边长（旧寻路代码中的 CELL）
# 注意：勿覆盖三维竞技场的 CELL（0.58）；二维请用 CELL_2D / 下方别名
MAP_CELL = CELL_2D
