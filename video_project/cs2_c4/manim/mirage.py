# rainbow_yu — CS2 C4 成片：Mirage 冲击波与地图 bundle

from __future__ import annotations

import numpy as np
from manim import *

from yty_manim.basic_unit.cs2_map import (
    BAKE_PSEUDOCODE,
    BOMB_SITE_A,
    BOMB_SITE_B,
    CELL_COLORS,
    CONNECTOR,
    CT_SPAWN,
    DEBUG_CONSOLE,
    DEMO_MARKERS,
    GAMEINFO_BOMB_PIPELINE,
    GAMEINFO_PATH,
    GRID_H,
    GRID_W,
    HAS_BAKED_DAMAGE,
    JUNGLE,
    MAP_NAME,
    MARKERS,
    MirageVectorMap,
    PATCH_NOTES_EN,
    RUNTIME_CODE_STEPS,
    RUNTIME_PSEUDOCODE,
    T_SPAWN,
    VPK_BOMB_RESOURCE,
    WALKABLE,
    WAVE_SPEED_GRID,
    WAVE_SPEED_M_S,
    arrival_time_seconds,
    bind_fluid_wave_tracker,
    dijkstra_wave_field,
    grid_dist_to_meters,
    grid_to_norm,
    intensity_to_damage,
    norm_to_grid,
    rgb_to_hex,
    sample_at,
    shockwave_field,
)
from yty_manim.disposition.fonts_and_colors import text_font


def _safe_ui_font() -> str:
    try:
        from manim.utils.fonts import get_available_fonts
        available = set(get_available_fonts())
        for name in ("Microsoft YaHei", "SimHei", "Noto Sans CJK SC", *text_font, "Sans"):
            if name in available:
                return name
    except Exception:
        pass
    return "Sans"


UI_FONT = _safe_ui_font()

__all__ = (
    "IntroHookScene",
    "OldVsNewBombScene",
    "PatchTimelineScene",
    "SourcePipelineScene",
    "GameEvidenceScene",
    "ThreePositionScene",
    "MapBakeBFSScene",
    "RuntimeLookupScene",
    "DamagePreviewHUDScene",
    "DamageCurveScene",
    "MirageShockwaveScene",
    "OutroScene",
    "CustomMapShockwaveScene",
    "CustomMapStaticScene",
)

# --- Visual constants (4:3 matches 128×96 radar grid) ---
MAP_W, MAP_H = 12.0, 9.0
C_BG = "#060608"
C_FLOOR = "#3a3a42"
C_FLOOR_EDGE = "#4a4a55"
C_SITE_A = "#8f3f3f"
C_SITE_B = "#7a3535"
C_CT = "#3f668f"
C_T = "#b8a452"
C_WALK = "#1a2332"
C_WAVE_HOT = "#ff6b35"
C_WAVE_MID = "#f7c548"
C_WAVE_COOL = "#4ecdc4"
C_GLOW = "#ff3366"

# Demo layout — map left, HUD right (no overlap)
DEMO_MAP_SCALE = 0.68
DEMO_MAP_SHIFT = LEFT * 3.05 + DOWN * 0.05
DEMO_HUD_X = 3.35

# Per-cell vector map (same 128×96 grid as Dijkstra / baked_field)
CELL_GAP = 0.04


def _norm_to_scene(nx: float, ny: float) -> np.ndarray:
    return np.array([nx * MAP_W - MAP_W / 2, ny * MAP_H - MAP_H / 2, 0])


def _map_transform(pt: np.ndarray, scale: float = DEMO_MAP_SCALE, shift: np.ndarray = DEMO_MAP_SHIFT) -> np.ndarray:
    return pt * scale + shift


def _cell_size() -> tuple[float, float]:
    return MAP_W / GRID_W * (1.0 - CELL_GAP), MAP_H / GRID_H * (1.0 - CELL_GAP)


def _cell_center_norm(i: int, j: int) -> tuple[float, float]:
    return i / (GRID_W - 1), j / (GRID_H - 1)


def _cell_zone_color(i: int, j: int) -> str | None:
    """Tint bomb sites / spawns on top of sampled radar colors."""
    nx, ny = _cell_center_norm(i, j)
    zones = (
        (BOMB_SITE_A, C_SITE_A, 0.048),
        (BOMB_SITE_B, C_SITE_B, 0.042),
        (CT_SPAWN, C_CT, 0.058),
        (T_SPAWN, C_T, 0.052),
    )
    for site, color, radius in zones:
        if (nx - site.norm[0]) ** 2 + (ny - site.norm[1]) ** 2 < radius ** 2:
            return color
    return None


def _cell_floor_color(i: int, j: int) -> str:
    zone = _cell_zone_color(i, j)
    if zone:
        return zone
    if CELL_COLORS is not None:
        r, g, b = (int(v) for v in CELL_COLORS[j, i])
        lum = 0.299 * r + 0.587 * g + 0.114 * b
        if lum < 24:
            return C_BG
        return rgb_to_hex(
            int(r * 0.82 + 38),
            int(g * 0.82 + 38),
            int(b * 0.82 + 42),
        )
    return C_FLOOR


def _make_cell_rect(i: int, j: int, color: str, *, opacity: float = 1.0, stroke_width: float = 0.0, stroke_color: str = C_GLOW) -> Rectangle:
    cw, ch = _cell_size()
    rect = Rectangle(
        width=cw,
        height=ch,
        stroke_width=stroke_width,
        stroke_color=stroke_color,
        fill_color=color,
        fill_opacity=opacity,
    )
    rect.move_to(_norm_to_scene(*_cell_center_norm(i, j)))
    return rect


def _build_vector_floor() -> VGroup:
    """One rectangle per walkable cell — shape matches radar grid."""
    cells = VGroup()
    for j in range(GRID_H):
        for i in range(GRID_W):
            if not WALKABLE[j, i]:
                continue
            color = _cell_floor_color(i, j)
            rect = _make_cell_rect(i, j, color, opacity=0.94, stroke_width=0.35, stroke_color=C_FLOOR_EDGE)
            cells.add(rect)
    return cells


def intensity_color(t: float) -> str:
    if t <= 0:
        return C_WALK
    if t < 0.35:
        c = interpolate_color(ManimColor(C_WAVE_COOL), ManimColor(C_WAVE_MID), t / 0.35)
    else:
        c = interpolate_color(ManimColor(C_WAVE_MID), ManimColor(C_WAVE_HOT), (t - 0.35) / 0.65)
    return c.to_hex()


def _load_shockwave_fields(source_norm=BOMB_SITE_A.norm):
    return shockwave_field(source_norm)


class MirageMap(VGroup):
    """Vector Mirage grid + per-cell shockwave (Dijkstra / baked_field algorithm view)."""

    def __init__(
        self,
        dist: np.ndarray | None = None,
        intensity: np.ndarray | None = None,
        wave_radius: float | None = None,
        cell_opacity: float = 0.75,
        markers: tuple = DEMO_MARKERS,
        show_marker_labels: bool = False,
        show_wave_front: bool = True,
        wave_front_band: float = 0.55,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.dist_field = dist
        self.intensity_field = intensity
        self.wave_radius = wave_radius
        self._markers = markers
        self._cell_opacity = cell_opacity
        self._show_marker_labels = show_marker_labels
        self._show_wave_front = show_wave_front
        self._wave_front_band = wave_front_band

        self.bg = Rectangle(
            width=MAP_W,
            height=MAP_H,
            fill_color=C_BG,
            fill_opacity=1,
            stroke_color=GREY_B,
            stroke_width=2.0,
        )
        self.floor = _build_vector_floor()
        self.heat, self._heat_cells = self._init_heat_layer()
        self.wave_front, self._front_cells = self._init_wave_front_layer()
        self.labels = self._build_zone_labels() if show_marker_labels else VGroup()
        self.add(self.bg, self.floor, self.heat, self.wave_front, self.labels)
        self.set_wave_radius(wave_radius)

    def _init_heat_layer(self) -> tuple[VGroup, dict[tuple[int, int], Rectangle]]:
        """One persistent rect per walkable cell — positions never move after init."""
        cells = VGroup()
        index: dict[tuple[int, int], Rectangle] = {}
        for j in range(GRID_H):
            for i in range(GRID_W):
                if not WALKABLE[j, i]:
                    continue
                rect = _make_cell_rect(i, j, C_WALK, opacity=0.0, stroke_width=0.0)
                cells.add(rect)
                index[(i, j)] = rect
        return cells, index

    def _init_wave_front_layer(self) -> tuple[VGroup, dict[tuple[int, int], Rectangle]]:
        cells = VGroup()
        index: dict[tuple[int, int], Rectangle] = {}
        for j in range(GRID_H):
            for i in range(GRID_W):
                if not WALKABLE[j, i]:
                    continue
                rect = _make_cell_rect(
                    i,
                    j,
                    C_GLOW,
                    opacity=0.0,
                    stroke_width=0.0,
                    stroke_color=C_GLOW,
                )
                cells.add(rect)
                index[(i, j)] = rect
        return cells, index

    def _build_zone_labels(self) -> VGroup:
        tags = VGroup()
        for site in self._markers:
            lbl = Text(site.label_cn, font=UI_FONT, font_size=13, color=WHITE)
            lbl.move_to(_norm_to_scene(*site.norm) + UP * 0.2)
            tags.add(lbl)
        return tags

    def make_marker(self, site, color=YELLOW, label: str = "") -> VGroup:
        pos = _norm_to_scene(*site.norm)
        ring = Circle(radius=0.1, color=color, stroke_width=2.5).move_to(pos)
        dot = Dot(pos, radius=0.055, color=color)
        grp: Mobject = VGroup(ring, dot)
        if label:
            tag = Text(label, font=UI_FONT, font_size=12, color=color)
            tag.next_to(ring, DOWN, buff=0.06)
            grp = VGroup(grp, tag)
        return grp

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

        show_front = (
            self._show_wave_front
            and has_field
            and radius is not None
            and radius > 0
        )
        band = self._wave_front_band
        for (i, j), rect in self._front_cells.items():
            if not show_front:
                rect.set_stroke(width=0.0, opacity=0.0)
                continue
            d = self.dist_field[j, i]
            if not np.isfinite(d) or abs(d - radius) > band:
                rect.set_stroke(width=0.0, opacity=0.0)
                continue
            rect.set_stroke(color=C_GLOW, width=2.4, opacity=0.95)


def bind_wave_tracker(mirage: MirageMap, wave_t: ValueTracker) -> MirageMap:
    mirage.set_wave_radius(wave_t.get_value())
    mirage.add_updater(lambda m: m.set_wave_radius(wave_t.get_value()))
    return mirage


def make_code_panel(code: str, title: str = "", font_size: int = 16) -> VGroup:
    body = Text(code, font="Consolas", font_size=font_size, line_spacing=0.9, color=GREY_A)
    body.set(max_width=5.8)
    bg = RoundedRectangle(corner_radius=0.12, width=body.width + 0.5, height=body.height + 0.45, color=GREY_E, fill_opacity=0.95, stroke_color=TEAL, stroke_width=1.5)
    bg.move_to(body)
    grp = VGroup(bg, body)
    if title:
        hdr = Text(title, font=UI_FONT, font_size=20, color=TEAL).next_to(bg, UP, buff=0.12)
        grp = VGroup(hdr, grp)
    return grp


def make_code_step_panel(step_title: str, code: str, font_size: int = 15) -> VGroup:
    hdr = Text(step_title, font=UI_FONT, font_size=18, color=TEAL)
    body = Text(code, font="Consolas", font_size=font_size, line_spacing=0.95, color=GREY_A)
    body.set(max_width=4.6)
    bg = RoundedRectangle(
        corner_radius=0.1,
        width=max(body.width, 4.2) + 0.4,
        height=body.height + 0.35,
        color=GREY_E,
        fill_opacity=0.96,
        stroke_color=GREY_D,
        stroke_width=1.2,
    )
    body.move_to(bg)
    grp = VGroup(hdr, VGroup(bg, body)).arrange(DOWN, buff=0.1, aligned_edge=LEFT)
    return grp


class IntroHookScene(Scene):
    def construct(self):
        self.camera.background_color = "#0d1117"
        dist, intensity = dijkstra_wave_field(BOMB_SITE_A.norm)
        wave_t = ValueTracker(0.0)
        max_d = float(np.nanmax(dist[np.isfinite(dist)]))

        mirage = bind_wave_tracker(
            MirageMap(dist=dist, intensity=intensity, wave_radius=wave_t.get_value()),
            wave_t,
        )
        mirage.scale(0.62).shift(LEFT * 2.2 + DOWN * 0.35)

        pip_hint = RoundedRectangle(
            width=5.8, height=6.2, corner_radius=0.08,
            stroke_color=GREY_D, stroke_width=2, fill_opacity=0.06, fill_color=BLACK,
        ).shift(RIGHT * 3.4)
        pip_lbl = Text("实机 PiP 区域", font=UI_FONT, font_size=22, color=GREY_B).move_to(pip_hint)

        title = Text("CS2 · de_mirage · C4 冲击波", font=UI_FONT, font_size=46, color=ORANGE)
        title.to_edge(UP, buff=0.35)
        sub = Text("Season 5 · 预计算波前传播", font=UI_FONT, font_size=28, color=GREY_B).next_to(title, DOWN, buff=0.15)

        self.add(mirage, pip_hint, pip_lbl)
        self.play(FadeIn(title, shift=DOWN * 0.2), FadeIn(sub), run_time=1.2)
        self.play(wave_t.animate.set_value(max_d * 0.85), run_time=6.0, rate_func=smooth)
        self.wait(3)
        self.play(FadeOut(title), FadeOut(sub), run_time=0.8)
        self.wait(1.5)


class OldVsNewBombScene(Scene):
    def construct(self):
        self.camera.background_color = "#0d1117"
        title = Text("C4 伤害：旧球体 vs 新波前", font=UI_FONT, font_size=38).to_edge(UP)
        self.play(FadeIn(title))

        dist, intensity = dijkstra_wave_field(BOMB_SITE_A.norm)
        mirage = MirageMap(dist=dist, intensity=intensity, wave_radius=999).scale(0.55).shift(RIGHT * 2.8 + DOWN * 0.2)
        bomb = mirage.make_marker(BOMB_SITE_A, ORANGE)
        jungle_m = mirage.make_marker(JUNGLE, GREEN)
        mirage.add(bomb, jungle_m)

        left_title = Text("旧：欧氏距离", font=UI_FONT, font_size=24, color=RED).shift(LEFT * 3.2 + UP * 2.2)
        sphere = Circle(radius=2.2, color=RED, stroke_width=2, fill_opacity=0.12).shift(LEFT * 3.2 + DOWN * 0.3)
        sphere.set_fill(RED, opacity=0.15)
        wall = Line(LEFT * 4.2 + DOWN * 0.8, LEFT * 2.2 + DOWN * 0.8, color=WHITE, stroke_width=4)
        thru = Text("穿墙同伤", font=UI_FONT, font_size=22, color=RED_A).next_to(wall, DOWN)

        right_title = Text("新：Mirage 路径波", font=UI_FONT, font_size=24, color=TEAL).shift(RIGHT * 2.8 + UP * 2.5)

        self.play(FadeIn(left_title), Create(wall), Create(sphere), FadeIn(thru))
        self.play(FadeIn(right_title), FadeIn(mirage), run_time=1.5)

        wave_t = ValueTracker(0.0)
        max_d = float(np.nanmax(dist[np.isfinite(dist)]))

        dyn = bind_wave_tracker(
            MirageMap(dist=dist, intensity=intensity, wave_radius=wave_t.get_value()),
            wave_t,
        )
        dyn.scale(0.55).shift(RIGHT * 2.8 + DOWN * 0.2)
        dyn.add(dyn.make_marker(BOMB_SITE_A, ORANGE), dyn.make_marker(JUNGLE, GREEN))
        self.remove(mirage)
        self.add(dyn)
        self.play(wave_t.animate.set_value(max_d), run_time=3.5, rate_func=smooth)
        safe = Text("Jungle：波被墙阻断", font=UI_FONT, font_size=22, color=GREEN).next_to(dyn, DOWN)
        self.play(FadeIn(safe))
        self.wait(3)


class PatchTimelineScene(Scene):
    def construct(self):
        self.camera.background_color = "#0d1117"
        heading = Text("官方补丁 · C4 冲击波", font=UI_FONT, font_size=40).to_edge(UP)
        quote = Text(PATCH_NOTES_EN, font=UI_FONT, font_size=22, color=TEAL, line_spacing=1.1)
        quote.set(max_width=11).next_to(heading, DOWN, buff=0.5)

        items = VGroup(
            Text("2026-07-08  Premier Season 5", font=UI_FONT, font_size=26, color=YELLOW),
            Text("baked_bomb_damage 写入每张爆破图", font=UI_FONT, font_size=24),
            Text("冲击波外扩 · 到达才结算", font=UI_FONT, font_size=24),
            Text("血条闪烁预览剩余 HP", font=UI_FONT, font_size=24),
            Text("2026-07-10  热修复", font=UI_FONT, font_size=26, color=YELLOW),
            Text("移除全图最低 1 伤害", font=UI_FONT, font_size=24),
            Text("修复地图区域边界查表", font=UI_FONT, font_size=24),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.28).next_to(quote, DOWN, buff=0.45)

        path = Text(VPK_BOMB_RESOURCE, font="Consolas", font_size=20, color=GREY_B).to_edge(DOWN, buff=0.5)
        self.play(Write(heading), FadeIn(quote, shift=UP * 0.15))
        for it in items:
            self.play(FadeIn(it, shift=RIGHT * 0.12), run_time=0.55)
        self.play(Write(path))
        self.wait(5)


class SourcePipelineScene(Scene):
    """Shows actual gameinfo.gi compile step + links to vdata path."""

    def construct(self):
        self.camera.background_color = "#0d1117"
        title = Text("真实源码：地图编译管线", font=UI_FONT, font_size=36).to_edge(UP)
        path_lbl = Text(GAMEINFO_PATH, font="Consolas", font_size=22, color=GREY_B).next_to(title, DOWN, buff=0.2)

        code = make_code_panel(GAMEINFO_BOMB_PIPELINE, "GameSpecificPostMapBuildSteps", font_size=20)
        code.scale(0.95).shift(LEFT * 3 + DOWN * 0.2)

        arrow = Arrow(code.get_right(), code.get_right() + RIGHT * 2.2, color=TEAL, buff=0.15)
        vdata = make_code_panel(
            f'Resource:\n"{VPK_BOMB_RESOURCE}"\n\nFields:\n  arrival\n  damage_power',
            "de_mirage.vpk",
            font_size=18,
        ).next_to(arrow, RIGHT, buff=0.1)

        self.play(FadeIn(title), FadeIn(path_lbl))
        self.play(FadeIn(code, shift=UP * 0.2))
        self.play(GrowArrow(arrow), FadeIn(vdata, shift=RIGHT * 0.2), run_time=1.2)
        box = SurroundingRectangle(code[1][2:4] if len(code) > 1 else code, color=ORANGE, buff=0.08)
        self.play(Create(box))
        self.wait(3)


class GameEvidenceScene(Scene):
    def construct(self):
        self.camera.background_color = "#0d1117"
        title = Text("实机 ↔ 文件联动", font=UI_FONT, font_size=36).to_edge(UP)
        cmd = Text(DEBUG_CONSOLE, font="Consolas", font_size=32, color=GREEN).next_to(title, DOWN, buff=0.35)

        dist, intensity = dijkstra_wave_field(BOMB_SITE_A.norm)
        mirage = MirageMap(dist=dist, intensity=intensity, wave_radius=999)
        mirage.scale(0.68).shift(DOWN * 0.45 + RIGHT * 0.8)

        note = Text("与 cl_bake_bomb_damage_debug 地面 overlay 同源", font=UI_FONT, font_size=22, color=TEAL)
        note.to_edge(DOWN, buff=0.45)
        res = Text(VPK_BOMB_RESOURCE, font="Consolas", font_size=18, color=GREY_B).next_to(note, UP, buff=0.15)

        cmd_panel = make_code_panel(
            f"{DEBUG_CONSOLE}\n\n# A 点伤害场 overlay\n# 数据来自 de_mirage.vpk",
            "控制台",
            font_size=16,
        ).scale(0.85).to_corner(UL).shift(DOWN * 1.0 + RIGHT * 0.2)

        self.play(FadeIn(title), FadeIn(cmd_panel))
        self.play(FadeIn(cmd), run_time=0.8)
        self.play(FadeIn(mirage, scale=0.9), run_time=2.0)
        self.play(mirage.animate.scale(1.08), run_time=3.0, rate_func=there_and_back)
        self.play(Write(res), FadeIn(note))
        self.wait(5)


class ThreePositionScene(Scene):
    def construct(self):
        self.camera.background_color = "#0d1117"
        title = Text("Mirage A 点 · 三站位伤害", font=UI_FONT, font_size=36).to_edge(UP)
        dist, intensity = dijkstra_wave_field(BOMB_SITE_A.norm)

        mirage = MirageMap(dist=dist, intensity=intensity, wave_radius=999).scale(0.65).shift(DOWN * 0.35)
        sites = [BOMB_SITE_A, CONNECTOR, JUNGLE]
        colors = [RED, ORANGE, GREEN]
        markers = VGroup()
        cards = VGroup()

        for site, col in zip(sites, colors):
            m = mirage.make_marker(site, col)
            markers.add(m)
            _, inten, dmg, _ = sample_at(site, dist, intensity)
            card = VGroup(
                Text(site.label_cn, font=UI_FONT, font_size=22, color=col),
                Text(f"强度 {inten:.0%}  →  {dmg} HP", font=UI_FONT, font_size=20),
            ).arrange(DOWN, buff=0.08, aligned_edge=LEFT)
            cards.add(card)
        cards.arrange(DOWN, aligned_edge=LEFT, buff=0.35).to_corner(UR).shift(DOWN * 0.5 + LEFT * 0.2)
        mirage.add(markers)

        self.play(FadeIn(title), FadeIn(mirage, run_time=1.5))
        for m, c in zip(markers, cards):
            self.play(FadeIn(m, scale=1.3), FadeIn(c, shift=LEFT * 0.2), run_time=0.9)
            self.play(Indicate(m, color=WHITE, scale_factor=1.15), Indicate(c), run_time=0.7)
            self.wait(0.8)
        foot = Text("护甲无效 · 路径决定伤害", font=UI_FONT, font_size=22, color=GREY_B).to_edge(DOWN)
        self.play(FadeIn(foot))
        self.wait(5)


class MapBakeBFSScene(Scene):
    def construct(self):
        self.camera.background_color = "#0d1117"
        title = Text("算法 ①  编译时 Dijkstra 烘焙", font=UI_FONT, font_size=34).to_edge(UP)
        sub = Text(f"{MAP_NAME} · A site → baked_bomb_damage.vdata", font=UI_FONT, font_size=22, color=GREY_B)
        sub.next_to(title, DOWN, buff=0.12)

        dist, intensity = dijkstra_wave_field(BOMB_SITE_A.norm)
        max_d = float(np.nanmax(dist[np.isfinite(dist)]))
        wave_t = ValueTracker(0.0)

        code = make_code_panel(BAKE_PSEUDOCODE, "cs2_bomb_damage", font_size=14).scale(0.82).to_corner(DL).shift(UP * 0.3)

        mirage = bind_wave_tracker(
            MirageMap(dist=dist, intensity=intensity, wave_radius=wave_t.get_value(), cell_opacity=0.95),
            wave_t,
        )
        mirage.scale(0.62).shift(RIGHT * 1.2 + DOWN * 0.25)
        mirage.add(mirage.make_marker(BOMB_SITE_A, ORANGE))
        self.play(FadeIn(title), FadeIn(sub), FadeIn(code))
        self.add(mirage)

        def map_xform(pt):
            return pt * 0.62 + RIGHT * 1.2 + DOWN * 0.25

        center = map_xform(_norm_to_scene(*BOMB_SITE_A.norm))

        def glow_rings():
            r = wave_t.get_value() / max(max_d, 1)
            grp = VGroup()
            for k in range(4):
                rad = 0.2 + (r * 4.5) + k * 0.18
                op = max(0, 0.45 - k * 0.1 - r * 0.15)
                c = Circle(radius=rad, color=C_GLOW, stroke_width=2.5).move_to(center)
                c.set_stroke(opacity=op)
                grp.add(c)
            return grp

        rings = always_redraw(glow_rings)
        self.add(rings)

        hl = SurroundingRectangle(code[1], color=ORANGE, buff=0.05)
        self.play(Create(hl))
        self.play(wave_t.animate.set_value(max_d), run_time=6, rate_func=smooth)
        save = Text("→ baked_bomb_damage.vdata", font="Consolas", font_size=22, color=TEAL).to_edge(DOWN)
        self.play(FadeIn(save))
        self.wait(2)


class RuntimeLookupScene(Scene):
    def construct(self):
        self.camera.background_color = "#0d1117"
        title = Text("算法 ②  运行时查表 + 波前推进", font=UI_FONT, font_size=34).to_edge(UP)
        dist, intensity = dijkstra_wave_field(BOMB_SITE_A.norm)
        max_d = float(np.nanmax(dist[np.isfinite(dist)]))
        conn_d, _, conn_dmg, conn_t = sample_at(CONNECTOR, dist, intensity)

        wave_t = ValueTracker(0.0)
        code = make_code_panel(RUNTIME_PSEUDOCODE, "client logic (inferred)", font_size=13).scale(0.78).to_corner(DR)

        mirage = bind_wave_tracker(
            MirageMap(dist=dist, intensity=intensity, wave_radius=wave_t.get_value()),
            wave_t,
        )
        mirage.scale(0.58).shift(LEFT * 2.6 + DOWN * 0.2)
        mirage.add(mirage.make_marker(BOMB_SITE_A, ORANGE), mirage.make_marker(CONNECTOR, YELLOW))
        self.play(FadeIn(title), FadeIn(code), FadeIn(mirage))

        tracker_lbl = always_redraw(
            lambda: Text(
                f"wave_front = {wave_t.get_value():.1f}  /  conn = {conn_d:.1f}  ({conn_t:.2f}s)",
                font="Consolas",
                font_size=20,
                color=YELLOW,
            ).to_corner(UL).shift(DOWN * 1.1)
        )
        self.add(tracker_lbl)
        self.play(wave_t.animate.set_value(conn_d), run_time=2.8, rate_func=smooth)
        dmg_txt = Text(f"-{conn_dmg} HP", font=UI_FONT, font_size=40, color=RED).shift(LEFT * 2.6 + DOWN * 2.2)
        self.play(FadeIn(dmg_txt, scale=1.4), Flash(dmg_txt, color=RED))
        hl = SurroundingRectangle(code[1], color=RED, buff=0.04)
        self.play(Create(hl))
        self.play(wave_t.animate.set_value(max_d * 0.95), run_time=2.5, rate_func=smooth)
        self.wait(2)


class DamagePreviewHUDScene(Scene):
    def construct(self):
        self.camera.background_color = "#0d1117"
        title = Text("算法 ③  settings_damage_prediction", font=UI_FONT, font_size=32).to_edge(UP)
        dist, intensity = dijkstra_wave_field(BOMB_SITE_A.norm)
        _, inten, dmg, _ = sample_at(CONNECTOR, dist, intensity)
        remain = max(0, 100 - dmg)

        mirage = MirageMap(dist=dist, intensity=intensity, wave_radius=999).scale(0.5).to_corner(DL).shift(UP * 0.2)
        mirage.add(mirage.make_marker(CONNECTOR, YELLOW))

        bar_w = 5.2
        bg = RoundedRectangle(width=bar_w, height=0.38, corner_radius=0.06, color=WHITE, fill_opacity=0.15)
        yellow = Rectangle(width=bar_w * remain / 100, height=0.38, fill_color=YELLOW, stroke_width=0)
        red = Rectangle(width=bar_w * dmg / 100, height=0.38, fill_color=RED, stroke_width=0)
        yellow.align_to(bg, LEFT)
        red.next_to(yellow, RIGHT, buff=0)
        hud = VGroup(bg, yellow, red).shift(RIGHT * 2 + UP * 0.5)

        code_line = Text("preview_hp = health - field[pos].damage_power", font="Consolas", font_size=20, color=TEAL)
        code_line.next_to(hud, UP, buff=0.35)
        vals = Text(f"Connect ·  -{dmg} HP  →  剩余 {remain}", font=UI_FONT, font_size=24).next_to(hud, DOWN, buff=0.25)

        self.play(FadeIn(title), FadeIn(mirage))
        self.play(FadeIn(hud), Write(code_line))
        self.play(DrawBorderThenFill(yellow), DrawBorderThenFill(red), FadeIn(vals), run_time=1.2)
        for _ in range(3):
            self.play(Indicate(red, color=RED_A), Indicate(yellow, color=YELLOW_A), run_time=0.6)
            self.wait(0.35)
        self.wait(4)


class DamageCurveScene(Scene):
    def construct(self):
        self.camera.background_color = "#0d1117"
        title = Text("Mirage A · damage_power 标定曲线", font=UI_FONT, font_size=32).to_edge(UP)
        self.play(FadeIn(title))

        axes = Axes(
            x_range=[0, 1, 0.2], y_range=[0, 120, 20],
            x_length=7.5, y_length=4.2,
            axis_config={"include_numbers": False, "font_size": 20},
            x_axis_config={"include_numbers": False, "numbers_to_include": []},
            y_axis_config={"include_numbers": False, "numbers_to_include": []},
        ).shift(DOWN * 0.35)
        x_ticks = VGroup(*[
            Text(f"{v:.1f}" if v < 1 else "1.0", font=UI_FONT, font_size=16).next_to(axes.c2p(v, 0), DOWN, buff=0.12)
            for v in (0, 0.2, 0.4, 0.6, 0.8, 1.0)
        ])
        y_ticks = VGroup(*[
            Text(str(v), font=UI_FONT, font_size=16).next_to(axes.c2p(0, v), LEFT, buff=0.12)
            for v in (0, 20, 40, 60, 80, 100, 120)
        ])
        x_lbl = Text("强度", font=UI_FONT, font_size=20).next_to(axes.x_axis, DOWN, buff=0.2)
        y_lbl = Text("HP 损失", font=UI_FONT, font_size=20).next_to(axes.y_axis, LEFT, buff=0.2)
        pts = [axes.c2p(i / 10, min(intensity_to_damage(i / 10), 120)) for i in range(11)]
        graph = VMobject(color=TEAL, stroke_width=5)
        graph.set_points_smoothly(pts)

        self.play(Create(axes), FadeIn(x_ticks), FadeIn(y_ticks), FadeIn(x_lbl), FadeIn(y_lbl), run_time=1.0)
        self.play(Create(graph), run_time=2.5, rate_func=smooth)
        for inten, lbl in ((0.2, "33"), (0.4, "77")):
            d = Dot(axes.c2p(inten, intensity_to_damage(inten)), color=YELLOW, radius=0.08)
            t = Text(f"{int(inten*100)}% → {lbl} HP", font=UI_FONT, font_size=22, color=YELLOW).next_to(d, UP)
            self.play(FadeIn(d, scale=1.5), Write(t), run_time=0.7)
            self.wait(0.4)
        note = Text("【实测·社区标定近似】护甲无效", font=UI_FONT, font_size=20, color=GREY_B).to_edge(DOWN)
        self.play(FadeIn(note))
        self.wait(4)


class MirageShockwaveScene(Scene):
    """Vector Mirage map (official radar + fluid contour wave) + baked vdata damage."""

    def construct(self):
        self.camera.background_color = "#0d1117"
        dist, intensity, damage = _load_shockwave_fields()
        max_d = float(np.nanmax(dist[np.isfinite(dist)]))

        samples = {}
        for site in (CONNECTOR, JUNGLE, CT_SPAWN):
            samples[site.name] = sample_at(site, dist, intensity, damage)

        wave_t = ValueTracker(0.0)

        mirage = MirageVectorMap(
            dist=dist,
            intensity=intensity,
            wave_radius=wave_t.get_value(),
            cell_opacity=0.82,
            show_wave_front=True,
        )
        mirage.scale(DEMO_MAP_SCALE).shift(DEMO_MAP_SHIFT)
        mirage.add(mirage.make_marker(BOMB_SITE_A, ORANGE, "C4"))
        for site, col in ((CONNECTOR, YELLOW), (JUNGLE, GREEN), (CT_SPAWN, TEAL)):
            mirage.add(mirage.make_marker(site, col))
        bind_fluid_wave_tracker(mirage, wave_t)

        # --- Header (top, full width) ---
        title = Text("de_mirage · A 点 C4 冲击波", font=UI_FONT, font_size=34, color=ORANGE)
        data_src = "baked_bomb_damage.vdata · 官方烘焙" if HAS_BAKED_DAMAGE else "Dijkstra 近似"
        sub = Text(
            f"WAVE_SPEED ≈ {WAVE_SPEED_M_S} m/s   arrival = dist / WAVE_SPEED   ·   {data_src}",
            font="Consolas",
            font_size=15,
            color=GREY_B,
        )
        header = VGroup(title, sub).arrange(DOWN, buff=0.1).to_edge(UP, buff=0.25)

        # --- Right HUD: stats + code steps (never overlaps map) ---
        stat_title = Text("站位采样", font=UI_FONT, font_size=20, color=WHITE)
        stat_rows = VGroup()
        for site, col in ((CONNECTOR, YELLOW), (JUNGLE, GREEN), (CT_SPAWN, TEAL)):
            d, inten, dmg, arr = samples[site.name]
            row = Text(
                f"{site.label_cn}  {grid_dist_to_meters(d):.0f}m  t={arr:.1f}s  -{dmg}HP",
                font=UI_FONT,
                font_size=15,
                color=GREY_B,
            )
            stat_rows.add(row)
        stat_rows.arrange(DOWN, aligned_edge=LEFT, buff=0.14)
        stats_block = VGroup(stat_title, stat_rows).arrange(DOWN, aligned_edge=LEFT, buff=0.18)

        code_title = Text("baked_bomb_damage.vdata", font="Consolas", font_size=17, color=TEAL)
        step_panels = VGroup(
            *[make_code_step_panel(t, c, font_size=13) for t, c in RUNTIME_CODE_STEPS]
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.22)
        for idx, panel in enumerate(step_panels):
            panel.set_opacity(0.25 if idx > 0 else 1.0)

        hud = VGroup(stats_block, code_title, step_panels).arrange(DOWN, aligned_edge=LEFT, buff=0.28)
        hud.move_to(RIGHT * DEMO_HUD_X + UP * 0.15)

        vpath = Text(VPK_BOMB_RESOURCE, font="Consolas", font_size=14, color=GREY_B).to_edge(DOWN, buff=0.25)

        wave_readout = always_redraw(
            lambda: Text(
                f"wave_front = {grid_dist_to_meters(wave_t.get_value()):.0f}m",
                font="Consolas",
                font_size=15,
                color=YELLOW,
            ).next_to(mirage, DOWN, buff=0.12)
        )

        self.add(mirage, wave_readout, vpath)
        self.play(FadeIn(header), FadeIn(hud), run_time=1.2)

        conn_d, _, _, conn_t = samples["connector"]
        jungle_d, _, _, jungle_t = samples["jungle"]
        ct_d, _, _, ct_t = samples["ct"]

        def highlight_step(n: int):
            for idx, panel in enumerate(step_panels):
                panel.set_opacity(1.0 if idx <= n else 0.22)
                bg = panel[1][0]
                bg.set_stroke(ORANGE if idx == n else GREY_D, width=2.5 if idx == n else 1.2)

        def highlight_stat(idx: int):
            for i, row in enumerate(stat_rows):
                row.set_color([YELLOW, GREEN, TEAL][i] if i == idx else GREY_B)

        highlight_step(0)
        self.play(Indicate(step_panels[0], color=ORANGE, scale_factor=1.02), run_time=0.8)
        self.wait(1.0)

        # ① wave expands toward connector
        self.play(wave_t.animate.set_value(conn_d), run_time=max(conn_t * 1.2, 2.0), rate_func=linear)
        highlight_step(1)
        highlight_stat(0)
        self.play(FadeIn(step_panels[1], shift=UP * 0.08), Indicate(stat_rows[0]), run_time=0.9)
        self.wait(1.2)

        # ② jungle
        self.play(
            wave_t.animate.set_value(jungle_d),
            run_time=max((jungle_t - conn_t) * 1.2, 1.5),
            rate_func=linear,
        )
        highlight_stat(1)
        self.play(Indicate(stat_rows[1]), run_time=0.6)
        self.wait(1.0)

        # ③ CT + damage apply
        self.play(
            wave_t.animate.set_value(ct_d),
            run_time=max((ct_t - jungle_t) * 1.2, 1.5),
            rate_func=linear,
        )
        highlight_step(2)
        highlight_stat(2)
        self.play(FadeIn(step_panels[2], shift=UP * 0.08), Indicate(stat_rows[2]), run_time=0.9)
        self.wait(1.0)

        # finish wave + preview UI
        self.play(wave_t.animate.set_value(max_d * 0.95), run_time=3.5, rate_func=smooth)
        highlight_step(3)
        self.play(FadeIn(step_panels[3], shift=UP * 0.08), run_time=0.8)
        self.wait(0.8)

        dmg_tags = VGroup()
        for site in (CONNECTOR, JUNGLE, CT_SPAWN):
            _, _, dmg, _ = samples[site.name]
            pos = _map_transform(_norm_to_scene(*site.norm))
            tag = Text(f"-{dmg}", font=UI_FONT, font_size=22, color=RED)
            tag.move_to(pos + UP * 0.28)
            dmg_tags.add(tag)
        self.play(LaggedStart(*[FadeIn(t, scale=1.3) for t in dmg_tags], lag_ratio=0.25))
        self.wait(4)


class OutroScene(Scene):
    def construct(self):
        self.camera.background_color = "#0d1117"
        dist, intensity = dijkstra_wave_field(BOMB_SITE_A.norm)
        wave_t = ValueTracker(0.0)
        max_d = float(np.nanmax(dist[np.isfinite(dist)]))

        mirage = bind_wave_tracker(
            MirageMap(dist=dist, intensity=intensity, wave_radius=wave_t.get_value()),
            wave_t,
        )
        mirage.scale(0.7).shift(DOWN * 0.4)
        self.add(mirage)

        lines = VGroup(
            Text("预计算 · O(1) 查表 · 路径生存", font=UI_FONT, font_size=38, color=TEAL),
            Text(VPK_BOMB_RESOURCE, font="Consolas", font_size=20, color=GREY_B),
        ).arrange(DOWN, buff=0.35).to_edge(UP, buff=0.45)

        credits = VGroup(
            Text("参考资料", font=UI_FONT, font_size=22, color=GREY_B),
            Text("Valve Season 5 Patch · HLTV · Dust2.us · SkinSniper", font=UI_FONT, font_size=16, color=GREY_D),
            Text("cl_bake_bomb_damage_debug 1  ·  本地验证", font=UI_FONT, font_size=16, color=GREY_D),
        ).arrange(DOWN, buff=0.12).to_edge(DOWN, buff=0.35)

        self.play(FadeIn(lines), wave_t.animate.set_value(max_d), run_time=5, rate_func=smooth)
        self.wait(2)
        self.play(FadeIn(credits, shift=UP * 0.15))
        self.wait(4)


# Backward-compatible aliases for edit script
GameEvidencePlaceholderScene = GameEvidenceScene
ThreePositionPlaceholderScene = ThreePositionScene

# ── 自定义 MapBundle 冲击波 ─────────────────────────────────

import os
from pathlib import Path

import numpy as np
from manim import *

from yty_manim.basic_unit.cs2_map import bind_wave_tracker, build_map_view_from_bundle
from yty_manim.tools.map_editor.map_bundle import MapBundle, default_maps_dir
from yty_manim.tools.map_editor.map_wave import grid_dist_to_meters, shockwave_field


def _resolve_bundle_path() -> Path:
    env = os.environ.get("MAP_BUNDLE")
    if env:
        p = Path(env)
        if p.is_dir():
            return p
    maps = default_maps_dir()
    saved = sorted(maps.iterdir()) if maps.exists() else []
    for p in saved:
        if p.is_dir() and (p / "meta.json").exists():
            return p
    blank = MapBundle.blank("demo_map")
    blank.save()
    return blank.bundle_dir


def _safe_font() -> str:
    try:
        from manim.utils.fonts import get_available_fonts
        available = set(get_available_fonts())
        for name in ("Microsoft YaHei", "SimHei", "Noto Sans CJK SC", "Sans"):
            if name in available:
                return name
    except Exception:
        pass
    return "Sans"


UI_FONT = _safe_font()


class CustomMapShockwaveScene(Scene):
    """Load exported map bundle and animate shockwave from primary explosion source."""

    def construct(self):
        self.camera.background_color = "#0d1117"
        bundle = MapBundle.load(_resolve_bundle_path())
        source = bundle.primary_explosion()
        if source is None:
            msg = Text("地图无爆炸源，请在编辑器中放置", font=UI_FONT, font_size=36, color=RED)
            self.add(msg)
            self.wait(2)
            return

        dist, intensity, _ = shockwave_field(bundle, source.norm)
        max_d = float(np.nanmax(dist[np.isfinite(dist)]))
        wave_t = ValueTracker(0.0)

        map_view = build_map_view_from_bundle(
            bundle,
            source_norm=source.norm,
            wave_radius=wave_t.get_value(),
            cell_opacity=0.8,
            ui_font=UI_FONT,
        )
        map_view.scale(0.85).shift(DOWN * 0.2)
        bind_wave_tracker(map_view, wave_t)

        title = Text(bundle.map_name, font=UI_FONT, font_size=40, color=ORANGE)
        sub = Text(
            f"爆炸源: {source.label}   WAVE_SPEED = {bundle.wave_speed_m_s} m/s",
            font=UI_FONT,
            font_size=22,
            color=GREY_B,
        )
        header = VGroup(title, sub).arrange(DOWN, buff=0.12).to_edge(UP, buff=0.3)

        readout = always_redraw(
            lambda: Text(
                f"wave_front = {grid_dist_to_meters(bundle, wave_t.get_value()):.0f} m",
                font="Consolas",
                font_size=18,
                color=YELLOW,
            ).next_to(map_view, DOWN, buff=0.15)
        )

        self.add(map_view, readout)
        self.play(FadeIn(header), run_time=0.8)
        self.play(wave_t.animate.set_value(max_d * 0.95), run_time=5.0, rate_func=smooth)
        self.wait(1.5)
        self.play(FadeOut(header), run_time=0.6)
        self.wait(0.5)


class CustomMapStaticScene(Scene):
    """Static preview of exported map (no animation)."""

    def construct(self):
        self.camera.background_color = "#0d1117"
        bundle = MapBundle.load(_resolve_bundle_path())
        map_view = build_map_view_from_bundle(bundle, wave_radius=999.0, ui_font=UI_FONT)
        map_view.scale(0.9)
        title = Text(f"{bundle.map_name} · 地图预览", font=UI_FONT, font_size=36, color=WHITE)
        title.to_edge(UP, buff=0.35)
        self.add(map_view, title)
        self.wait(2)
