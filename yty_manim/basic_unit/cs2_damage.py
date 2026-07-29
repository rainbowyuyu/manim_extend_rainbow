# rainbow_yu manim_extend.basic_unit.cs2_damage 🐋✨
# CS2 爆炸伤害：预烘焙教学组件 + 三维伤害丘

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from manim import *

from yty_manim.disposition.fonts_and_colors import (
    CODE_FONT,
    UI_FONT,
    cs2_damage,
    cs2_damage_hill,
    cs2_map_heat,
)

__all__ = (
    "intensity_color",
    "ExplosionMarker",
    "ExplosionSource",
    "PlayerMarker",
    "DamageGrid",
    "HealthBar",
    "FormulaPanel",
    "WallSpec",
    "DamageHill3D",
    "bake_damage_field",
    "bake_distance_only_field",
    "bilinear_sample",
    "nearest_sample",
    "compute_damage",
    "predicted_health",
    "make_demo_walls",
    "make_grid_points",
    "map_frame",
    "caption",
    "fm",
)



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

# ── 预烘焙教学组件 ──────────────────────────────────────────

"""教学模型（非 Valve 实装）：距离衰减 + 遮挡材质 × 网格烘焙 × 双线性采样 × 血条预览。"""




# ── 视觉 / 教学默认值（见 disposition.fonts_and_colors）────────────────
C_BG = cs2_damage["C_BG"]
C_TITLE = cs2_damage["C_TITLE"]
C_SUB = cs2_damage["C_SUB"]
C_MUTED = cs2_damage["C_MUTED"]
C_PANEL = cs2_damage["C_PANEL"]
C_PANEL_EDGE = cs2_damage["C_PANEL_EDGE"]
C_MAP = cs2_damage["C_MAP"]
C_WALL = cs2_damage["C_WALL"]
C_WOOD = cs2_damage["C_WOOD"]
C_BLAST = cs2_damage["C_BLAST"]
C_BLAST_GLOW = cs2_damage["C_BLAST_GLOW"]
C_HEAT_HI = cs2_damage["C_HEAT_HI"]
C_HEAT_MID = cs2_damage["C_HEAT_MID"]
C_HEAT_LO = cs2_damage["C_HEAT_LO"]
C_HP = cs2_damage["C_HP"]
C_HP_PREVIEW = cs2_damage["C_HP_PREVIEW"]
C_PLAYER_A = cs2_damage["C_PLAYER_A"]
C_PLAYER_B = cs2_damage["C_PLAYER_B"]
C_PLAYER_C = cs2_damage["C_PLAYER_C"]
C_ACCENT = cs2_damage["C_ACCENT"]
C_WARN = cs2_damage["C_WARN"]

MAP_W, MAP_H = cs2_damage["MAP_W"], cs2_damage["MAP_H"]
MAP_ORIGIN = np.array(cs2_damage["MAP_ORIGIN"])
GRID_NX, GRID_NY = cs2_damage["GRID_NX"], cs2_damage["GRID_NY"]
D_MAX = cs2_damage["D_MAX"]
RADIUS = cs2_damage["RADIUS"]
HP_MAX = cs2_damage["HP_MAX"]
HP_START = cs2_damage["HP_START"]

MAT_OPEN = cs2_damage["MAT_OPEN"]
MAT_WOOD = cs2_damage["MAT_WOOD"]
MAT_BRICK = cs2_damage["MAT_BRICK"]
MAT_CONCRETE = cs2_damage["MAT_CONCRETE"]


def fm(tex_or_ascii: str, font_size: int = 24, color: str = C_TITLE) -> Text:
    """公式文本：无 LaTeX 时用 Unicode 数学排版（下标/乘号/平方）。"""
    s = tex_or_ascii
    if "\\" in s or "{" in s:
        s = (
            s.replace(r"\mathbf{", "")
            .replace(r"\mathrm{", "")
            .replace(r"\operatorname{", "")
            .replace(r"D_{\max}", "Dₘₐₓ")
            .replace(r"D_{\mathrm{max}}", "Dₘₐₓ")
            .replace(r"H_{\mathrm{after}}", "H′")
            .replace(r"H_{after}", "H′")
            .replace(r"D_{\mathrm{sample}}", "Dₛ")
            .replace(r"D_{sample}", "Dₛ")
            .replace(r"\left", "")
            .replace(r"\right", "")
            .replace(r"\to", "→")
            .replace(r"\cdot", "·")
            .replace(r"\,", " ")
            .replace(r"\!", "")
            .replace(r"\sqrt", "√")
            .replace(r"\max", "max")
            .replace("{", "")
            .replace("}", "")
            .replace("\\", "")
        )
    s = (
        s.replace("D_max", "Dₘₐₓ")
        .replace("H_after", "H′")
        .replace("D_sample", "Dₛ")
        .replace("*(", " · (")
        .replace("*", " · ")
        .replace("^2", "²")
        .replace("->", "→")
        .replace("u=d/R", "u = d / R")
        .replace("u = d/R", "u = d / R")
    )
    font = UI_FONT if any(ord(c) > 127 for c in s) else CODE_FONT
    return Text(s, font=font, font_size=font_size, color=color)


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(value, high))


def distance_attenuation(distance: float, radius: float, max_damage: float) -> float:
    if radius <= 0:
        return 0.0
    u = clamp(distance / radius, 0.0, 1.0)
    return max_damage * (1.0 - u) ** 2


def linear_attenuation(distance: float, radius: float, max_damage: float) -> float:
    u = clamp(distance / radius, 0.0, 1.0)
    return max_damage * (1.0 - u)


def _segment_samples(a: np.ndarray, b: np.ndarray, n: int = 48) -> np.ndarray:
    t = np.linspace(0.0, 1.0, n)
    return a[None, :] * (1 - t)[:, None] + b[None, :] * t[:, None]


@dataclass
class WallSpec:
    x0: float
    y0: float
    x1: float
    y1: float
    material: float
    label: str = ""
    color: str = C_WALL

    def contains(self, p: np.ndarray) -> bool:
        return self.x0 <= p[0] <= self.x1 and self.y0 <= p[1] <= self.y1

    def as_rect(self) -> Rectangle:
        w, h = self.x1 - self.x0, self.y1 - self.y0
        r = Rectangle(
            width=w,
            height=h,
            fill_color=self.color,
            fill_opacity=0.92,
            stroke_color="#8a96a8",
            stroke_width=1.2,
        )
        r.move_to([(self.x0 + self.x1) / 2, (self.y0 + self.y1) / 2, 0])
        return r


def visibility_factor(
    explosion_point: np.ndarray,
    sample_point: np.ndarray,
    walls: list[WallSpec],
    n_samples: int = 48,
) -> float:
    """教学模型：线段采样 × 材质透过；非真实引擎碰撞查询。"""
    a = np.asarray(explosion_point, dtype=float)[:2]
    b = np.asarray(sample_point, dtype=float)[:2]
    pts = _segment_samples(a, b, n_samples)
    vis = 1.0
    hit: set[int] = set()
    for p in pts:
        for idx, wall in enumerate(walls):
            if idx in hit:
                continue
            if wall.contains(p):
                hit.add(idx)
                vis *= wall.material
                if vis <= 1e-6:
                    return 0.0
    return float(vis)


def compute_damage(
    explosion_point: np.ndarray,
    sample_point: np.ndarray,
    radius: float,
    max_damage: float,
    walls: list[WallSpec],
) -> float:
    d = float(np.linalg.norm(np.asarray(sample_point)[:2] - np.asarray(explosion_point)[:2]))
    return distance_attenuation(d, radius, max_damage) * visibility_factor(
        explosion_point, sample_point, walls
    )


def bake_damage_field(
    grid_points: np.ndarray,
    explosion_point: np.ndarray,
    radius: float,
    max_damage: float,
    walls: list[WallSpec],
) -> np.ndarray:
    ny, nx = grid_points.shape[:2]
    field = np.zeros((ny, nx), dtype=float)
    for i in range(ny):
        for j in range(nx):
            field[i, j] = compute_damage(
                explosion_point, grid_points[i, j], radius, max_damage, walls
            )
    return field


def bake_distance_only_field(
    grid_points: np.ndarray,
    explosion_point: np.ndarray,
    radius: float,
    max_damage: float,
) -> np.ndarray:
    ny, nx = grid_points.shape[:2]
    field = np.zeros((ny, nx), dtype=float)
    e = np.asarray(explosion_point)[:2]
    for i in range(ny):
        for j in range(nx):
            d = float(np.linalg.norm(grid_points[i, j][:2] - e))
            field[i, j] = distance_attenuation(d, radius, max_damage)
    return field


def world_to_grid(
    x: float,
    y: float,
    x_min: float,
    x_max: float,
    y_min: float,
    y_max: float,
    nx: int,
    ny: int,
) -> tuple[float, float, int, int]:
    gx = (x - x_min) / max(x_max - x_min, 1e-9) * (nx - 1)
    gy = (y - y_min) / max(y_max - y_min, 1e-9) * (ny - 1)
    j0 = int(np.floor(clamp(gx, 0, nx - 1.0001)))
    i0 = int(np.floor(clamp(gy, 0, ny - 1.0001)))
    j0 = min(j0, nx - 2)
    i0 = min(i0, ny - 2)
    return gx, gy, j0, i0


def bilinear_sample(
    field: np.ndarray,
    x: float,
    y: float,
    x_min: float,
    x_max: float,
    y_min: float,
    y_max: float,
) -> tuple[float, float, float, float, float, float, float]:
    ny, nx = field.shape
    gx, gy, j0, i0 = world_to_grid(x, y, x_min, x_max, y_min, y_max, nx, ny)
    s = gx - j0
    t = gy - i0
    d00 = float(field[i0, j0])
    d10 = float(field[i0, j0 + 1])
    d01 = float(field[i0 + 1, j0])
    d11 = float(field[i0 + 1, j0 + 1])
    d0 = (1 - s) * d00 + s * d10
    d1 = (1 - s) * d01 + s * d11
    return (1 - t) * d0 + t * d1, s, t, d00, d10, d01, d11


def nearest_sample(
    field: np.ndarray,
    x: float,
    y: float,
    x_min: float,
    x_max: float,
    y_min: float,
    y_max: float,
) -> float:
    ny, nx = field.shape
    gx = (x - x_min) / max(x_max - x_min, 1e-9) * (nx - 1)
    gy = (y - y_min) / max(y_max - y_min, 1e-9) * (ny - 1)
    j = int(round(clamp(gx, 0, nx - 1)))
    i = int(round(clamp(gy, 0, ny - 1)))
    return float(field[i, j])


def predicted_health(current_health: float, sampled_damage: float, armor_factor: float = 1.0) -> float:
    return max(0.0, current_health - sampled_damage * armor_factor)


def heat_color(t: float) -> ManimColor:
    t = clamp(t, 0.0, 1.0)
    if t < 0.01:
        return ManimColor(C_MAP)
    if t < 0.35:
        return interpolate_color(ManimColor(C_HEAT_LO), ManimColor(C_HEAT_MID), t / 0.35)
    return interpolate_color(ManimColor(C_HEAT_MID), ManimColor(C_HEAT_HI), (t - 0.35) / 0.65)


def make_demo_walls() -> list[WallSpec]:
    return [
        WallSpec(-1.1, -0.4, -0.75, 2.1, MAT_CONCRETE, "混凝土", C_WALL),
        WallSpec(0.9, -1.2, 1.25, 1.4, MAT_CONCRETE, "混凝土", C_WALL),
        WallSpec(-0.2, 0.55, 0.85, 0.85, MAT_WOOD, "薄木板", C_WOOD),
        WallSpec(2.0, 0.2, 3.2, 0.55, MAT_BRICK, "砖墙", cs2_damage["C_BRICK"]),
    ]


def make_grid_points(nx: int = GRID_NX, ny: int = GRID_NY):
    pad = 0.25
    x_min, x_max = MAP_ORIGIN[0] + pad, MAP_ORIGIN[0] + MAP_W - pad
    y_min, y_max = MAP_ORIGIN[1] + pad, MAP_ORIGIN[1] + MAP_H - pad
    xs = np.linspace(x_min, x_max, nx)
    ys = np.linspace(y_min, y_max, ny)
    pts = np.zeros((ny, nx, 3))
    for i, y in enumerate(ys):
        for j, x in enumerate(xs):
            pts[i, j] = [x, y, 0]
    return pts, x_min, x_max, y_min, y_max


class ExplosionMarker(VGroup):
    """
    教学用爆炸源标记，
    继承于 :class:`~.VGroup` ，

    Notes
    -----

    - 与 ``tools.map_editor.map_bundle.ExplosionSource`` 数据类不同，本类仅用于画面
    - 兼容旧名 :data:`ExplosionSource`

    Examples
    --------

    >>> class MarkerDemo(Scene):
    >>>     def construct(self):
    >>>         self.add(ExplosionMarker(ORIGIN))

    """
    def __init__(self, center: np.ndarray, radius: float = RADIUS, **kwargs):
        super().__init__(**kwargs)
        self.center_pt = np.asarray(center, dtype=float)
        self.radius = radius
        self.core = Dot(self.center_pt, radius=0.1, color=C_BLAST)
        self.core.set_z_index(8)
        glow = Circle(radius=0.22, stroke_color=C_BLAST_GLOW, stroke_width=2.0, fill_opacity=0)
        glow.move_to(self.center_pt)
        self.ring = Circle(radius=radius, stroke_color=C_BLAST, stroke_width=1.6, stroke_opacity=0.55)
        self.ring.move_to(self.center_pt)
        self.ring.set_fill(opacity=0)
        label = fm("e", font_size=28, color=C_BLAST_GLOW)
        label.next_to(self.core, UR, buff=0.08)
        self.add(glow, self.ring, self.core, label)


class PlayerMarker(VGroup):
    def __init__(self, pos: np.ndarray, name: str, color: str = C_PLAYER_A, **kwargs):
        super().__init__(**kwargs)
        self.pos = np.asarray(pos, dtype=float)
        body = Circle(radius=0.18, fill_color=color, fill_opacity=0.95, stroke_color=WHITE, stroke_width=1.2)
        arrow = Triangle(fill_color=WHITE, fill_opacity=0.9, stroke_width=0).scale(0.07)
        arrow.rotate(-PI / 2)
        arrow.shift(RIGHT * 0.02)
        tag = Text(name, font=UI_FONT, font_size=16, color=color)
        tag.next_to(body, UP, buff=0.1)
        self.body = body
        self.add(body, arrow, tag)
        self.move_to(self.pos)

    def set_world_pos(self, p: np.ndarray) -> None:
        self.pos = np.asarray(p, dtype=float)
        self.move_to(self.pos)


class DamageGrid(Group):
    """
    预烘焙伤害点阵热力网格，
    继承于 :class:`~.Group` ，

    Notes
    -----

    - 使用 Group 而非 VGroup，避免空锚点 zip 异常
    - 配合 :func:`bake_damage_field` / :func:`bilinear_sample` 使用

    """

    def __init__(self, points: np.ndarray, field: np.ndarray | None = None, max_damage: float = D_MAX, **kwargs):
        super().__init__(**kwargs)
        self.points = points
        self.ny, self.nx = points.shape[:2]
        self.max_damage = max_damage
        dx = float(points[0, 1, 0] - points[0, 0, 0]) if self.nx > 1 else 0.4
        dy = float(points[1, 0, 1] - points[0, 0, 1]) if self.ny > 1 else 0.4
        r = 0.42 * min(dx, dy)
        self.cells: list[list[Dot]] = []
        for i in range(self.ny):
            row = []
            for j in range(self.nx):
                cell = Dot(points[i, j], radius=r, color=ManimColor(C_MAP))
                cell.set_opacity(0.35)
                row.append(cell)
                self.add(cell)
            self.cells.append(row)
        if field is not None:
            self.apply_field(field)

    def apply_field(self, field: np.ndarray, opacity_scale: float = 0.9) -> None:
        for i in range(self.ny):
            for j in range(self.nx):
                t = field[i, j] / max(self.max_damage, 1e-9)
                self.cells[i][j].set_color(heat_color(t))
                self.cells[i][j].set_opacity(0.15 + opacity_scale * max(t, 0.05))

    def set_cell(self, i: int, j: int, value: float) -> None:
        t = value / max(self.max_damage, 1e-9)
        self.cells[i][j].set_color(heat_color(t))
        self.cells[i][j].set_opacity(0.15 + 0.9 * max(t, 0.05))


class HealthBar(VGroup):
    def __init__(self, width: float = 4.2, height: float = 0.42, **kwargs):
        super().__init__(**kwargs)
        self.bar_w = width
        self.track = RoundedRectangle(
            width=width,
            height=height,
            corner_radius=0.08,
            fill_color="#151c28",
            fill_opacity=1,
            stroke_color=C_PANEL_EDGE,
            stroke_width=1.4,
        )
        self.hp_fill = RoundedRectangle(
            width=max(0.05, width * (HP_START / HP_MAX)),
            height=height - 0.06,
            corner_radius=0.06,
            fill_color=C_HP,
            fill_opacity=0.95,
            stroke_width=0,
        )
        self.preview = RoundedRectangle(
            width=0.05,
            height=height - 0.06,
            corner_radius=0.05,
            fill_color=C_HP_PREVIEW,
            fill_opacity=0.55,
            stroke_width=0,
        )
        self.hp_fill.move_to(self.track.get_left() + RIGHT * 0.03, aligned_edge=LEFT)
        self.preview.move_to(self.hp_fill.get_right(), aligned_edge=LEFT)
        self.val = Text(f"{HP_START:.0f}", font=CODE_FONT, font_size=22, color=C_TITLE)
        self.after = Text(f"{HP_START:.0f}", font=CODE_FONT, font_size=18, color=C_HP_PREVIEW)
        nums = VGroup(
            Text("HP", font=CODE_FONT, font_size=16, color=C_SUB),
            self.val,
            Text("->", font=CODE_FONT, font_size=16, color=C_MUTED),
            self.after,
        ).arrange(RIGHT, buff=0.12)
        nums.next_to(self.track, UP, buff=0.12).align_to(self.track, LEFT)
        self.lethal = Text("预计致死", font=UI_FONT, font_size=18, color=C_HP_PREVIEW)
        self.lethal.next_to(self.track, RIGHT, buff=0.2)
        self.lethal.set_opacity(0)
        self.nums = nums
        self.add(self.track, self.hp_fill, self.preview, nums, self.lethal)

    def update_values(self, hp: float, damage: float) -> None:
        hp = clamp(hp, 0, HP_MAX)
        after = predicted_health(hp, max(0.0, damage))
        lost = hp - after
        new_val = Text(f"{hp:.0f}", font=CODE_FONT, font_size=22, color=C_TITLE)
        new_after = Text(f"{after:.0f}", font=CODE_FONT, font_size=18, color=C_HP_PREVIEW)
        new_val.move_to(self.val)
        new_after.move_to(self.after)
        self.val.become(new_val)
        self.after.become(new_after)
        left = self.track.get_left()[0] + 0.03
        cy = self.track.get_center()[1]
        gw = max(0.04, self.bar_w * (after / HP_MAX))
        self.hp_fill.stretch_to_fit_width(gw)
        self.hp_fill.move_to([left, cy, 0], aligned_edge=LEFT)
        pw = max(0.04, self.bar_w * (lost / HP_MAX)) if lost > 0.5 else 0.04
        self.preview.stretch_to_fit_width(pw)
        self.preview.move_to(self.hp_fill.get_right(), aligned_edge=LEFT)
        self.preview.set_opacity(0.55 if lost > 0.5 else 0)
        self.lethal.set_opacity(1 if damage >= hp - 0.5 else 0)


class FormulaPanel(VGroup):
    def __init__(self, lines: list[str], title: str = "", width: float = 4.6, **kwargs):
        super().__init__(**kwargs)
        items = []
        if title:
            items.append(Text(title, font=UI_FONT, font_size=18, color=C_ACCENT))
        for line in lines:
            if any(ord(c) > 127 for c in line) and not line.isascii():
                items.append(Text(line, font=UI_FONT, font_size=16, color=C_TITLE))
            else:
                items.append(fm(line, font_size=20, color=C_TITLE))
        body = VGroup(*items).arrange(DOWN, buff=0.16, aligned_edge=LEFT)
        box = RoundedRectangle(
            width=max(width, body.width + 0.5),
            height=body.height + 0.4,
            corner_radius=0.12,
            fill_color=C_PANEL,
            fill_opacity=0.94,
            stroke_color=C_PANEL_EDGE,
            stroke_width=1.2,
        )
        body.move_to(box)
        self.add(box, body)


def map_frame() -> Rectangle:
    r = Rectangle(
        width=MAP_W,
        height=MAP_H,
        fill_color=C_MAP,
        fill_opacity=0.55,
        stroke_color="#8a96aa",
        stroke_width=1.6,
    )
    r.move_to(MAP_ORIGIN + np.array([MAP_W / 2, MAP_H / 2, 0]))
    return r


def caption(text: str) -> Text:
    t = Text(text, font=UI_FONT, font_size=18, color=C_SUB)
    t.set_width(min(t.width, 12.5))
    t.to_edge(DOWN, buff=0.28)
    return t


ExplosionSource = ExplosionMarker

# ── 三维伤害丘 ──────────────────────────────────────────────

# 覆盖预烘焙 C_BG：伤害丘场景使用独立背景色
C_BG = cs2_damage_hill["C_BG"]
C_DOT = cs2_damage_hill["C_DOT"]
C_TRAIL = cs2_damage_hill["C_TRAIL"]
C_CORE = cs2_damage_hill["C_CORE"]
C_LETHAL = cs2_damage_hill["C_LETHAL"]

# 峰顶红 → 山腰黄绿 → 山脚青绿蓝
def _height_to_color(t: float) -> ManimColor:
    """t∈[0,1]：0=边沿绿蓝，1=峰顶红。"""
    t = float(np.clip(t, 0.0, 1.0))
    stops = [(u, ManimColor(c)) for u, c in cs2_damage_hill["HEIGHT_STOPS"]]
    for i in range(len(stops) - 1):
        t0, c0 = stops[i]
        t1, c1 = stops[i + 1]
        if t <= t1:
            u = 0.0 if t1 <= t0 else (t - t0) / (t1 - t0)
            return interpolate_color(c0, c1, u)
    return stops[-1][1]


X_MIN, X_MAX = cs2_damage_hill["X_MIN"], cs2_damage_hill["X_MAX"]
Y_MIN, Y_MAX = cs2_damage_hill["Y_MIN"], cs2_damage_hill["Y_MAX"]
R_LETHAL = cs2_damage_hill["R_LETHAL"]
R_BLAST = cs2_damage_hill["R_BLAST"]
Z_SCALE = cs2_damage_hill["Z_SCALE"]


def _smoothstep(edge0: float, edge1: float, x: float) -> float:
    t = np.clip((x - edge0) / (edge1 - edge0 + 1e-9), 0.0, 1.0)
    return float(t * t * (3.0 - 2.0 * t))


def _damage_raw(x: float, y: float) -> float:
    """中心致死平台 + 外圈衰减 + 不规则起伏。"""
    r = float(np.hypot(x, y))
    if r <= R_LETHAL:
        base = 1.0
    else:
        t = _smoothstep(R_LETHAL, R_BLAST, r)
        base = (1.0 - t) ** 1.25

    bumpy = (
        0.11 * np.sin(1.55 * x + 0.35) * np.cos(1.25 * y - 0.25)
        + 0.08 * np.sin(2.55 * x - 1.0) * np.sin(2.05 * y + 0.55)
        + 0.055 * np.cos(3.2 * x + 0.85 * y)
        + 0.05 * np.exp(-((x - 1.35) ** 2 + (y + 0.85) ** 2) / 0.7)
        - 0.07 * np.exp(-((x + 1.15) ** 2 + (y - 0.65) ** 2) / 0.45)
        + 0.04 * np.exp(-((x - 0.4) ** 2 + (y - 1.7) ** 2) / 0.55)
        - 0.045 * np.exp(-((x + 0.2) ** 2 + (y + 1.5) ** 2) / 0.5)
    )
    edge = _smoothstep(0.4, R_BLAST * 0.92, r)
    center_flat = 1.0 - 0.5 * (1.0 - _smoothstep(0.0, R_LETHAL * 1.1, r))
    h = base + bumpy * (0.4 + 0.6 * edge) * center_flat
    return float(np.clip(h, 0.0, 1.12))


def _height(x: float, y: float) -> float:
    return _damage_raw(x, y) * Z_SCALE


def _color_surface_by_height(surface: Surface) -> None:
    """按面片高度上色，保证红→绿蓝渐变可见。"""
    z_lo, z_hi = 0.0, Z_SCALE * 1.05
    for face in surface.submobjects:
        z = float(face.get_center()[2])
        t = (z - z_lo) / (z_hi - z_lo + 1e-9)
        col = _height_to_color(t)
        face.set_fill(col, opacity=0.95)
        face.set_stroke(color=col, width=0.15, opacity=0.12)


def _bezier_xy(
    p0: np.ndarray,
    p1: np.ndarray,
    p2: np.ndarray,
    p3: np.ndarray,
    n: int = 80,
) -> np.ndarray:
    ts = np.linspace(0.0, 1.0, n)
    pts = []
    for t in ts:
        u = 1.0 - t
        xy = u**3 * p0 + 3 * u**2 * t * p1 + 3 * u * t**2 * p2 + t**3 * p3
        pts.append(xy)
    return np.asarray(pts, dtype=float)


def _curved_descent_path() -> np.ndarray:
    """首尾带弯曲的下滑轨迹，贴合曲面高度。"""
    # 起点：致死圈外缘附近；终点：外圈低伤区；中段侧向弯曲
    p0 = np.array([1.15, 0.55])
    p1 = np.array([1.55, 1.55])   # 开头拐向一侧
    p2 = np.array([2.85, 0.35])   # 中后段回弯
    p3 = np.array([3.35, 1.45])   # 结尾再弯向外
    xy = _bezier_xy(p0, p1, p2, p3, n=90)
    pts = []
    for x, y in xy:
        pts.append([float(x), float(y), _height(float(x), float(y)) + 0.11])
    return np.asarray(pts, dtype=float)


class DamageHill3D:
    """
    三维爆炸伤害丘（高度场 + 着色 + 下滑轨迹），
    教学曲面工具，非引擎实装。

    Notes
    -----

    - ``height(x, y)`` 给出曲面高度；``color_surface`` 按面片高度上色
    - ``curved_descent_path`` 返回贴地的贝塞尔下滑采样点

    Examples
    --------

    >>> hill = DamageHill3D()
    >>> z = hill.height(1.0, 0.5)
    >>> pts = hill.curved_descent_path()

    """

    def __init__(
            self,
            r_lethal: float = R_LETHAL,
            r_blast: float = R_BLAST,
            z_scale: float = Z_SCALE,
    ):
        self.r_lethal = r_lethal
        self.r_blast = r_blast
        self.z_scale = z_scale

    @staticmethod
    def height_to_color(t: float) -> ManimColor:
        return _height_to_color(t)

    def damage_raw(self, x: float, y: float) -> float:
        return _damage_raw(x, y)

    def height(self, x: float, y: float) -> float:
        return self.damage_raw(x, y) * self.z_scale

    def color_surface(self, surface: Surface) -> None:
        _color_surface_by_height(surface)

    def curved_descent_path(self) -> np.ndarray:
        return _curved_descent_path()
