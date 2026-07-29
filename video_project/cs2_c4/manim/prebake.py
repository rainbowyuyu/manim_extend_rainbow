# rainbow_yu — CS2 C4 成片：预烘焙算法
"""Title → 动机 → 爆炸伤害教学桥 → CS2 写答卷 → 管线 → 运行查表.

去底栏字幕 · 左图右栏 · 图层不互挡 · 节奏可控。
承接第二章：不复述 Dijkstra；教学桥讲距离/衰减/遮挡/采样/血条。

Usage:
    python -m manim -qh video_project/cs2_c4/manim/prebake.py PrebakeAlgorithmScene
    python -m manim -qh video_project/cs2_c4/manim/prebake.py ExplosionPrebakeVisualization
"""

from __future__ import annotations

import heapq

import numpy as np
from manim import *

from yty_manim.basic_unit.cs2_arena import (
    BOMB_IJ,
    GRID,
    MAP_SCALE,
    MAP_SHIFT,
    SURVIVOR_IJ,
    GridMap2D,
    _heat_color,
)
from yty_manim.basic_unit.cs2_damage import (
    C_BLAST,
    C_BLAST_GLOW,
    C_HP_PREVIEW,
    C_PLAYER_A,
    C_PLAYER_B,
    C_PLAYER_C,
    C_WARN,
    D_MAX,
    GRID_NX,
    GRID_NY,
    HP_START,
    RADIUS,
    DamageGrid,
    ExplosionSource,
    HealthBar,
    PlayerMarker,
    bake_damage_field,
    bake_distance_only_field,
    bilinear_sample,
    compute_damage,
    fm,
    make_demo_walls,
    make_grid_points,
    map_frame,
    nearest_sample,
    predicted_health,
    visibility_factor,
)
from video_project.cs2_c4.manim.titles import play_prebake_title_card
from yty_manim.basic_unit.cs2_map import WAVE_SPEED_M_S, arrival_time_seconds
from yty_manim.disposition.fonts_and_colors import text_font

__all__ = (
    "PrebakeAlgorithmScene",
    "ExplosionPrebakeVisualization",
)

C_BG = "#07090f"
C_TITLE = "#f1f5ff"
C_SUB = "#a8b4c8"
C_MUTED = "#7a879c"
C_ACCENT = "#3de0c8"
C_BAKE = "#f0a040"
C_SAVE = "#5eead4"
C_RUNTIME = "#a78bfa"
C_BAD = "#ff6b6b"
C_GOOD = "#4ade80"
C_HOT = "#ff6b4a"
C_PANEL = "#0c121c"
C_PANEL_EDGE = "#2a3a55"

MAP_TRANSFORM = MAP_SCALE * 0.78
MAP_OFFSET = MAP_SHIFT + LEFT * 1.05 + DOWN * 0.05
RIGHT_BUFF = 0.85
FRAME_RIGHT_X = 6.55
FRAME_BOTTOM_Y = -3.4
Z_HEADER = 20
Z_PANEL = 12
Z_TEACH_PANEL = 16
Z_MAP = 4
Z_FIELD = 5
Z_WALL = 8
Z_MARKERS = 14
CODE_FONT = "Consolas"

# 教学地图压到左侧，右侧留给公式/血条
TEACH_SCALE = 0.58
TEACH_SHIFT = LEFT * 2.2 + DOWN * 0.12
TEACH_PANEL_X = 3.55

EASE = rate_functions.ease_in_out_cubic
RT_HEADER = 0.55
RT_SWAP = 0.8
RT_FADE = 0.55
RT_MAP = 0.85
BEAT = 1.05
HOLD = 1.65
HOLD_L = 2.1


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


def _walkable_cells() -> list[tuple[int, int]]:
    return [(i, j) for i in range(GRID.shape[0]) for j in range(GRID.shape[1]) if GRID[i, j]]


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


def _build_bake_fields(start: tuple[int, int]) -> tuple[np.ndarray, np.ndarray, np.ndarray, list[tuple[int, int]]]:
    dist = np.full(GRID.shape, np.inf)
    dist[start[0], start[1]] = 0.0
    pq: list[tuple[float, int, int]] = [(0.0, start[0], start[1])]
    order: list[tuple[int, int]] = []
    while pq:
        d, i, j = heapq.heappop(pq)
        if d > dist[i, j]:
            continue
        order.append((i, j))
        for ni, nj, w in _neighbors8(i, j):
            nd = d + w
            if nd < dist[ni, nj]:
                dist[ni, nj] = nd
                heapq.heappush(pq, (nd, ni, nj))
    finite = dist[np.isfinite(dist)]
    max_d = float(finite.max()) if finite.size else 1.0
    arrival = np.zeros_like(dist)
    damage = np.zeros_like(dist, dtype=np.int32)
    mask = np.isfinite(dist)
    arrival[mask] = np.array([arrival_time_seconds(d) for d in dist[mask]])
    for i, j in _walkable_cells():
        if not np.isfinite(dist[i, j]):
            continue
        t = float(np.clip(1.0 - dist[i, j] / max_d, 0, 1)) ** 0.82
        damage[i, j] = int(round(255 * t))
    return dist, arrival, damage, order


def _mono(text: str, font_size: int = 22, color: str = WHITE) -> Text:
    font = UI_FONT if any(ord(c) > 127 for c in text) else CODE_FONT
    return Text(text, font=font, font_size=font_size, color=color)


def _mixed_text(
    chunks: list[tuple[str, str]],
    *,
    font_size: int = 18,
    color: str = C_TITLE,
    buff: float = 0.1,
) -> VGroup:
    """ASCII 用等宽、中文用 UI 字体，避免 Consolas 缺字形变成白块。"""
    parts = []
    for text, kind in chunks:
        font = CODE_FONT if kind == "code" else UI_FONT
        parts.append(Text(text, font=font, font_size=font_size, color=color))
    return VGroup(*parts).arrange(RIGHT, buff=buff, aligned_edge=DOWN)


def _step_header(step: str, title: str, accent: str = C_TITLE) -> VGroup:
    """章节标题。step 为空时不显示编号徽章（教学子段用）。"""
    hdr = Text(title, font=UI_FONT, font_size=26, color=ManimColor(C_TITLE))
    hdr.set_color_by_gradient(ManimColor(accent), ManimColor(C_TITLE))
    rule = Line(ORIGIN, RIGHT * max(hdr.width * 0.42, 0.9), stroke_color=accent, stroke_width=2.4)
    rule.set_stroke(opacity=0.85)
    title_block = VGroup(hdr, rule).arrange(DOWN, buff=0.1, aligned_edge=LEFT)

    if step:
        badge = RoundedRectangle(
            width=0.62,
            height=0.36,
            corner_radius=0.08,
            fill_color=accent,
            fill_opacity=0.22,
            stroke_color=accent,
            stroke_width=1.2,
        )
        badge_lbl = Text(step, font=UI_FONT, font_size=16, color=accent)
        badge_lbl.move_to(badge)
        grp = VGroup(VGroup(badge, badge_lbl), title_block).arrange(RIGHT, buff=0.2, aligned_edge=UP)
    else:
        grp = title_block

    grp.to_edge(UP, buff=0.28)
    grp.set_z_index(Z_HEADER)
    return grp


def _info_card(title: str, lines: list[str], accent: str, width: float = 4.2) -> VGroup:
    t = Text(title, font=UI_FONT, font_size=17, color=ManimColor(accent))
    body = VGroup(*[Text(line, font=UI_FONT, font_size=14, color="#d8e2f0") for line in lines])
    body.arrange(DOWN, buff=0.08, aligned_edge=LEFT)
    content = VGroup(t, body).arrange(DOWN, buff=0.12, aligned_edge=LEFT)
    pad_x, pad_y = 0.3, 0.24
    box = RoundedRectangle(
        width=max(content.width + 2 * pad_x, width),
        height=content.height + 2 * pad_y,
        corner_radius=0.12,
        fill_color=C_PANEL,
        fill_opacity=0.95,
        stroke_color=C_PANEL_EDGE,
        stroke_width=1.2,
    )
    content.move_to(box.get_center())
    # 内容绝不超出框
    if content.width > box.width - 2 * pad_x:
        content.scale_to_fit_width(box.width - 2 * pad_x)
        content.move_to(box.get_center())
    grp = VGroup(box, content)
    grp.set_z_index(Z_PANEL)
    return grp


def _place_map(grid: GridMap2D) -> None:
    grid.apply_map_transform(MAP_TRANSFORM, MAP_OFFSET)
    grid.set_z_index(Z_MAP)
    grid.markers.set_z_index(Z_MARKERS)


def _place_right_panel(panel: Mobject, map_body: Mobject) -> Mobject:
    panel.next_to(map_body, RIGHT, buff=RIGHT_BUFF)
    panel.align_to(map_body, UP).shift(DOWN * 0.08)
    panel.set_z_index(Z_PANEL)
    return panel


def _fit_panel(panel: Mobject, map_body: Mobject, max_h_ratio: float = 0.88) -> Mobject:
    _place_right_panel(panel, map_body)
    max_h = map_body.height * max_h_ratio
    if panel.height > max_h:
        panel.scale(max_h / panel.height)
        _place_right_panel(panel, map_body)
    if panel.get_right()[0] > FRAME_RIGHT_X:
        panel.shift(LEFT * (panel.get_right()[0] - FRAME_RIGHT_X + 0.12))
    if panel.get_bottom()[1] < FRAME_BOTTOM_Y:
        panel.shift(UP * (FRAME_BOTTOM_Y - panel.get_bottom()[1]))
    return panel


def _color_cell(grid: GridMap2D, dist: np.ndarray, max_d: float, i: int, j: int) -> None:
    t = float(np.clip(1.0 - dist[i, j] / max_d, 0, 1)) if max_d > 0 else 0.5
    grid.tiles[(i, j)].set_fill(_heat_color(0.25 + 0.75 * (1.0 - t)), opacity=1)


def _icon_clock(color: str = C_HOT, r: float = 0.28) -> VGroup:
    ring = Circle(radius=r, stroke_color=color, stroke_width=2.2, fill_opacity=0)
    hand = Line(ORIGIN, UP * r * 0.55, stroke_color=color, stroke_width=2.0)
    hand2 = Line(ORIGIN, RIGHT * r * 0.35, stroke_color=color, stroke_width=1.6)
    return VGroup(ring, hand, hand2)


def _icon_person(color: str = C_SUB) -> VGroup:
    head = Dot(ORIGIN + UP * 0.14, radius=0.07, color=color)
    body = Line(UP * 0.05, DOWN * 0.18, stroke_color=color, stroke_width=2.2)
    return VGroup(head, body)


def _icon_search(color: str = C_HOT) -> VGroup:
    """折线路网示意。"""
    a = Dot(LEFT * 0.22 + DOWN * 0.1, radius=0.04, color=color)
    b = Dot(UP * 0.18, radius=0.035, color=color)
    c = Dot(RIGHT * 0.22 + DOWN * 0.05, radius=0.04, color=color)
    s1 = Line(a.get_center(), b.get_center(), stroke_color=color, stroke_width=1.8)
    s2 = Line(b.get_center(), c.get_center(), stroke_color=color, stroke_width=1.8)
    return VGroup(s1, s2, a, b, c)


def _icon_table(color: str = C_GOOD) -> VGroup:
    cells = VGroup()
    for i in range(2):
        for j in range(2):
            sq = Square(side_length=0.2, stroke_color=color, stroke_width=1.4, fill_opacity=0)
            sq.move_to(LEFT * 0.12 + RIGHT * 0.24 * j + UP * 0.12 + DOWN * 0.24 * i)
            cells.add(sq)
    cursor = SurroundingRectangle(cells[0], color=color, buff=0.02, stroke_width=2.0)
    return VGroup(cells, cursor)


def _mul() -> Text:
    return Text("×", font=CODE_FONT, font_size=22, color=C_MUTED)


def _formula_damage() -> VGroup:
    """D = D_max · (1 − u)² ，附 u = d / R。"""
    u_line = VGroup(
        Text("u", font=CODE_FONT, font_size=20, color=C_SUB),
        Text("=", font=CODE_FONT, font_size=20, color=C_MUTED),
        Text("d", font=CODE_FONT, font_size=20, color=C_SUB),
        Text("/", font=CODE_FONT, font_size=20, color=C_MUTED),
        Text("R", font=CODE_FONT, font_size=20, color=C_BLAST),
    ).arrange(RIGHT, buff=0.08)
    d_main = Text("D", font=CODE_FONT, font_size=30, color=C_TITLE)
    eq = Text("=", font=CODE_FONT, font_size=28, color=C_MUTED)
    d_base = Text("D", font=CODE_FONT, font_size=30, color=C_TITLE)
    d_sub = Text("max", font=CODE_FONT, font_size=14, color=C_TITLE)
    d_sub.next_to(d_base, DR, buff=0.02).shift(UP * 0.12 + LEFT * 0.02)
    dmax = VGroup(d_base, d_sub)
    rest = Text("· (1 − u)²", font=CODE_FONT, font_size=28, color=C_TITLE)
    body = VGroup(d_main, eq, dmax, rest).arrange(RIGHT, buff=0.12, aligned_edge=DOWN)
    grp = VGroup(u_line, body).arrange(DOWN, buff=0.22)
    grp.set_z_index(Z_TEACH_PANEL)
    return grp


def _formula_full_damage() -> VGroup:
    """D = D_max · (1−u)² · V(e, p)。"""
    d_main = Text("D", font=CODE_FONT, font_size=24, color=C_TITLE)
    eq = Text("=", font=CODE_FONT, font_size=22, color=C_MUTED)
    d_base = Text("D", font=CODE_FONT, font_size=24, color=C_TITLE)
    d_sub = Text("max", font=CODE_FONT, font_size=12, color=C_TITLE)
    d_sub.next_to(d_base, DR, buff=0.02).shift(UP * 0.1 + LEFT * 0.02)
    dmax = VGroup(d_base, d_sub)
    mid = Text("· (1 − u)² ·", font=CODE_FONT, font_size=22, color=C_TITLE)
    vis = Text("V(e, p)", font=CODE_FONT, font_size=22, color=C_ACCENT)
    return VGroup(d_main, eq, dmax, mid, vis).arrange(RIGHT, buff=0.1, aligned_edge=DOWN)


def _formula_health() -> VGroup:
    """H' = max(0, H - D_s)；避免 Consolas 缺字形白框（不用 Unicode 下标）。"""
    h = Text("H'", font=CODE_FONT, font_size=28, color=C_TITLE)
    eq = Text("=", font=CODE_FONT, font_size=26, color=C_MUTED)
    left = Text("max(0, H - ", font=CODE_FONT, font_size=26, color=C_TITLE)
    d_base = Text("D", font=CODE_FONT, font_size=26, color=C_TITLE)
    d_sub = Text("s", font=CODE_FONT, font_size=14, color=C_TITLE)
    d_sub.next_to(d_base, DR, buff=0.02).shift(UP * 0.1 + LEFT * 0.02)
    d_s = VGroup(d_base, d_sub)
    right = Text(")", font=CODE_FONT, font_size=26, color=C_TITLE)
    return VGroup(h, eq, left, d_s, right).arrange(RIGHT, buff=0.08, aligned_edge=DOWN)


def _cost_compare_visual() -> VGroup:
    """左右对照：任务块数量 + 耗时条，直观表达每帧工作量差异。"""
    bar_w = 3.4
    track_h = 0.28

    def _column(
        title: str,
        accent: str,
        tasks: VGroup,
        ops_text: str,
        bar_frac: float,
        time_text: str,
    ) -> VGroup:
        title_t = Text(title, font=UI_FONT, font_size=22, color=accent)
        ops = Text(ops_text, font=UI_FONT, font_size=15, color=C_SUB)
        track = RoundedRectangle(
            width=bar_w,
            height=track_h,
            corner_radius=0.07,
            fill_color="#151c2a",
            fill_opacity=1,
            stroke_color=C_PANEL_EDGE,
            stroke_width=1.0,
        )
        fill = RoundedRectangle(
            width=0.12,
            height=track_h,
            corner_radius=0.07,
            fill_color=accent,
            fill_opacity=0.9,
            stroke_width=0,
        )
        fill.move_to(track.get_left(), aligned_edge=LEFT)
        time_lbl = Text(time_text, font=CODE_FONT, font_size=18, color=accent)
        bar_row = VGroup(track, time_lbl).arrange(RIGHT, buff=0.16)
        body = VGroup(title_t, tasks, ops, bar_row).arrange(DOWN, buff=0.22)
        card = RoundedRectangle(
            width=max(5.2, body.width + 0.55),
            height=body.height + 0.55,
            corner_radius=0.14,
            fill_color=C_PANEL,
            fill_opacity=0.96,
            stroke_color=accent,
            stroke_width=1.8,
        )
        body.move_to(card)
        # 初始几乎不可见，贴在轨道左端（动画时用 updater 保左对齐）
        fill.stretch_to_fit_width(0.08)
        fill.move_to(track.get_left(), aligned_edge=LEFT)
        fill.set_opacity(0)
        body.add(fill)  # 随 body 一起变换，避免条漂出卡片
        grp = VGroup(card, body)
        grp.bar_fill = fill  # type: ignore[attr-defined]
        grp.bar_track = track  # type: ignore[attr-defined]
        grp.bar_width = bar_w  # type: ignore[attr-defined]
        grp.target_value = bar_frac  # type: ignore[attr-defined]
        grp.tasks = tasks  # type: ignore[attr-defined]
        return grp

    busy = VGroup()
    for _ in range(12):
        chip = RoundedRectangle(
            width=0.55,
            height=0.32,
            corner_radius=0.05,
            fill_color="#3a1a14",
            fill_opacity=0.95,
            stroke_color=C_HOT,
            stroke_width=1.2,
        )
        mark = _icon_search(C_HOT).scale(0.45)
        mark.move_to(chip)
        busy.add(VGroup(chip, mark))
    busy.arrange_in_grid(3, 4, buff=0.1)

    cell = Square(side_length=0.9, stroke_color=C_GOOD, stroke_width=2.0, fill_color="#143024", fill_opacity=0.95)
    cursor = SurroundingRectangle(cell, color=C_GOOD, buff=0.06, stroke_width=2.5)
    flash = Dot(ORIGIN, radius=0.12, color=C_GOOD).move_to(cell)
    lookup = VGroup(cell, cursor, flash)

    naive = _column("每帧重算", C_HOT, busy, "帧 × 玩家 × 路径搜索", 0.92, "~80×")
    smart = _column("每帧查表", C_GOOD, lookup, "一次采样读表", 0.12, "~1×")
    vs = Text("VS", font=CODE_FONT, font_size=22, color=C_MUTED)
    block = VGroup(naive, vs, smart).arrange(RIGHT, buff=0.4, aligned_edge=ORIGIN)
    block.naive = naive  # type: ignore[attr-defined]
    block.smart = smart  # type: ignore[attr-defined]
    return block


def _field_chip_row(name: str, accent: str, chips: list[str]) -> VGroup:
    """字段名固定槽宽 + 等宽数据芯片，避免长短错位/中文白框。"""
    label_w = 1.55
    slot = RoundedRectangle(
        width=label_w,
        height=0.36,
        corner_radius=0.06,
        fill_color="#121a28",
        fill_opacity=0.95,
        stroke_color=accent,
        stroke_width=1.2,
    )
    name_t = Text(name, font=CODE_FONT, font_size=15, color=accent)
    name_t.move_to(slot)
    if name_t.width > label_w - 0.16:
        name_t.scale_to_fit_width(label_w - 0.16)
        name_t.move_to(slot)

    boxes = VGroup()
    for s in chips:
        cell = RoundedRectangle(
            width=0.42,
            height=0.36,
            corner_radius=0.05,
            fill_color="#1a2436",
            fill_opacity=1,
            stroke_color=accent,
            stroke_width=1.0,
            stroke_opacity=0.55,
        )
        glyph = Text(s, font=CODE_FONT, font_size=12, color=accent)
        if glyph.width > 0.34:
            glyph.scale_to_fit_width(0.34)
        glyph.move_to(cell)
        boxes.add(VGroup(cell, glyph))
    boxes.arrange(RIGHT, buff=0.08)
    return VGroup(VGroup(slot, name_t), boxes).arrange(RIGHT, buff=0.16)


def _answer_sheet_card(n_cells: int) -> VGroup:
    """全图答卷：可视化芯片，内容严格落在框内；无底栏小字。"""
    title = Text("baked_field", font=CODE_FONT, font_size=18, color=C_BAKE)
    sub = Text("全图答卷", font=UI_FONT, font_size=15, color=C_SUB)

    mini = VGroup()
    cols, rows = 6, 4
    for r in range(rows):
        for c in range(cols):
            sq = Square(side_length=0.16, stroke_width=0)
            hot = (r + c) % 3 != 0
            sq.set_fill(C_BAKE if hot else "#1a2233", opacity=0.85 if hot else 0.45)
            sq.move_to(LEFT * 0.5 + RIGHT * 0.2 * c + UP * 0.28 + DOWN * 0.2 * r)
            mini.add(sq)
    count = Text(f"× {n_cells}", font=CODE_FONT, font_size=16, color=C_TITLE)
    grid_row = VGroup(mini, count).arrange(RIGHT, buff=0.2)

    arr_row = _field_chip_row("arrival", C_SAVE, ["t", ".", "2", "s"])
    dmg_row = _field_chip_row("damage", C_HOT, ["0", "-", "2", "5"])
    dmg_row[0].align_to(arr_row[0], LEFT)
    dmg_row[1].align_to(arr_row[1], LEFT)
    fields = VGroup(arr_row, dmg_row).arrange(DOWN, buff=0.18, aligned_edge=LEFT)

    content = VGroup(title, sub, grid_row, fields).arrange(DOWN, buff=0.16, aligned_edge=LEFT)
    pad_x, pad_y = 0.32, 0.28
    sheet = RoundedRectangle(
        width=content.width + 2 * pad_x,
        height=content.height + 2 * pad_y,
        corner_radius=0.14,
        fill_color=C_PANEL,
        fill_opacity=0.96,
        stroke_color=C_BAKE,
        stroke_width=1.8,
    )
    content.move_to(sheet.get_center())
    max_inner = sheet.width - 2 * pad_x
    if content.width > max_inner:
        content.scale_to_fit_width(max_inner)
        content.move_to(sheet.get_center())
    return VGroup(sheet, content)


def _trade_visual() -> VGroup:
    """空间换时间故事板：编译写表 → 交换 → 运行查表。

    子块互不重叠，分步 FadeIn；中英混排不用 Consolas 扛中文。
    """

    def _panel(w: float, h: float, accent: str) -> RoundedRectangle:
        return RoundedRectangle(
            width=w,
            height=h,
            corner_radius=0.14,
            fill_color=C_PANEL,
            fill_opacity=0.96,
            stroke_color=accent,
            stroke_width=1.8,
        )

    def _strip(label: str, accent: str, w: float = 2.45) -> VGroup:
        box = RoundedRectangle(
            width=w,
            height=0.42,
            corner_radius=0.08,
            fill_color="#121a28",
            fill_opacity=1.0,
            stroke_color=accent,
            stroke_width=1.4,
        )
        t = Text(label, font=CODE_FONT, font_size=15, color=accent)
        t.move_to(box)
        return VGroup(box, t)

    # ── 左：编译付一次 ──────────────────────────────────────────────
    left_card = _panel(3.75, 3.85, C_BAKE)
    left_title = Text("编译 · 付一次", font=UI_FONT, font_size=18, color=C_BAKE)
    left_title.next_to(left_card.get_top(), DOWN, buff=0.16)

    bake_grid = _mini_grid(4, 4, heat=True).scale(0.66)
    bake_bomb = Dot(bake_grid.get_corner(UL) + DR * 0.12, radius=0.05, color=C_HOT)
    bake_block = VGroup(bake_grid, bake_bomb)
    bake_cap = _mixed_text(
        [("全图 ", "ui"), ("Dijkstra", "code"), (" x 1", "ui")],
        font_size=13,
        color=C_SUB,
        buff=0.06,
    )
    bake_col = VGroup(bake_block, bake_cap).arrange(DOWN, buff=0.08)
    bake_col.next_to(left_title, DOWN, buff=0.16).set_x(left_card.get_center()[0])

    arr_strip = _strip("arrival[i,j]", C_SAVE)
    dmg_strip = _strip("damage[i,j]", C_HOT)
    disk_tag = Text("落盘答卷（占空间）", font=UI_FONT, font_size=13, color=C_BAKE)
    table_col = VGroup(arr_strip, dmg_strip, disk_tag).arrange(DOWN, buff=0.1)
    table_col.next_to(bake_col, DOWN, buff=0.18).set_x(left_card.get_center()[0])

    left_shell = VGroup(left_card, left_title, bake_col)
    left_col = VGroup(left_shell, table_col)

    # ── 中：交换桥 ──────────────────────────────────────────────────
    bridge_arrow = Arrow(
        LEFT * 0.7,
        RIGHT * 0.7,
        buff=0,
        stroke_width=3.4,
        color=C_ACCENT,
        max_tip_length_to_length_ratio=0.25,
    )
    bridge = VGroup(
        Text("空间换时间", font=UI_FONT, font_size=17, color=C_ACCENT),
        bridge_arrow,
        Text("付空间 · 买每帧时间", font=UI_FONT, font_size=12, color=C_MUTED),
    ).arrange(DOWN, buff=0.14)

    # ── 右：运行每帧省 ──────────────────────────────────────────────
    right_card = _panel(3.75, 3.85, C_GOOD)
    right_title = Text("运行 · 每帧省", font=UI_FONT, font_size=18, color=C_GOOD)
    right_title.next_to(right_card.get_top(), DOWN, buff=0.16)

    lut = _mini_grid(4, 4, heat=True).scale(0.66)
    cursor = SurroundingRectangle(lut[5], color=C_ACCENT, buff=0.03, stroke_width=2.2)
    player = Dot(lut[5].get_center(), radius=0.07, color=C_ACCENT)
    lut_cap = Text("坐标 → 下标", font=UI_FONT, font_size=13, color=C_SUB)
    lut_col = VGroup(VGroup(lut, cursor, player), lut_cap).arrange(DOWN, buff=0.08)
    lut_col.next_to(right_title, DOWN, buff=0.16).set_x(right_card.get_center()[0])

    # O(1) 与「查表」拆字体，杜绝 Consolas 缺字白块
    o1_txt = _mixed_text(
        [("O(1)", "code"), (" 查表", "ui")],
        font_size=18,
        color=C_GOOD,
        buff=0.08,
    )
    o1_badge = RoundedRectangle(
        width=max(o1_txt.width + 0.45, 1.9),
        height=0.58,
        corner_radius=0.1,
        fill_color="#12241c",
        fill_opacity=1.0,
        stroke_color=C_GOOD,
        stroke_width=2.0,
    )
    o1_txt.move_to(o1_badge)
    o1 = VGroup(o1_badge, o1_txt)

    # 查表读数（故事收束：点到哪格，读出什么）
    read_a = Text("arrival = 1.24s", font=CODE_FONT, font_size=14, color=C_SAVE)
    read_d = Text("damage  = 86", font=CODE_FONT, font_size=14, color=C_HOT)
    readout = VGroup(read_a, read_d).arrange(DOWN, buff=0.08, aligned_edge=LEFT)
    skip_tag = Text("跳过每帧搜路（省时间）", font=UI_FONT, font_size=13, color=C_GOOD)
    right_tail = VGroup(o1, readout, skip_tag).arrange(DOWN, buff=0.12)
    right_tail.next_to(lut_col, DOWN, buff=0.16).set_x(right_card.get_center()[0])

    right_shell = VGroup(right_card, right_title, lut_col)
    right_col = VGroup(right_shell, right_tail)

    mid = VGroup(left_col, bridge, right_col).arrange(RIGHT, buff=0.26)

    def _big_field(name: str, hint: str, accent: str) -> VGroup:
        """深色底 + 描边强调；文字单独高层，避免 Indicate/填充盖字。"""
        box = RoundedRectangle(
            width=4.6,
            height=1.05,
            corner_radius=0.12,
            fill_color=C_PANEL,
            fill_opacity=0.98,
            stroke_color=accent,
            stroke_width=2.0,
        )
        wash = RoundedRectangle(
            width=4.45,
            height=0.88,
            corner_radius=0.1,
            fill_color=accent,
            fill_opacity=0.10,
            stroke_width=0,
        )
        wash.move_to(box)
        n = Text(name, font=CODE_FONT, font_size=22, color=accent)
        h = Text(hint, font=UI_FONT, font_size=16, color=C_TITLE)
        inner = VGroup(n, h).arrange(RIGHT, buff=0.35)
        inner.move_to(box)
        if inner.width > box.width - 0.45:
            inner.scale_to_fit_width(box.width - 0.45)
            inner.move_to(box)
        wash.set_z_index(0)
        box.set_z_index(1)
        inner.set_z_index(3)
        card = VGroup(wash, box, inner)
        card.box = box  # type: ignore[attr-defined]
        card.inner = inner  # type: ignore[attr-defined]
        return card

    fields = VGroup(
        Text("答卷里存的两张表 — 故事的全部答案", font=UI_FONT, font_size=14, color=C_MUTED),
        VGroup(
            _big_field("arrival", "何时到达", C_SAVE),
            _big_field("damage", "扣多少血", C_HOT),
        ).arrange(RIGHT, buff=0.35),
    ).arrange(DOWN, buff=0.14)

    root = VGroup(mid, fields).arrange(DOWN, buff=0.26)
    root.left_shell = left_shell  # type: ignore[attr-defined]
    root.table_col = table_col  # type: ignore[attr-defined]
    root.arr_strip = arr_strip  # type: ignore[attr-defined]
    root.dmg_strip = dmg_strip  # type: ignore[attr-defined]
    root.bridge = bridge  # type: ignore[attr-defined]
    root.bridge_arrow = bridge_arrow  # type: ignore[attr-defined]
    root.right_shell = right_shell  # type: ignore[attr-defined]
    root.right_tail = right_tail  # type: ignore[attr-defined]
    root.o1 = o1  # type: ignore[attr-defined]
    root.readout = readout  # type: ignore[attr-defined]
    root.skip_tag = skip_tag  # type: ignore[attr-defined]
    root.lut = lut  # type: ignore[attr-defined]
    root.cursor = cursor  # type: ignore[attr-defined]
    root.player = player  # type: ignore[attr-defined]
    root.bake_grid = bake_grid  # type: ignore[attr-defined]
    root.fields = fields  # type: ignore[attr-defined]
    return root


def _mini_grid(cols: int = 4, rows: int = 4, heat: bool = False) -> VGroup:
    """管线站用的迷你地图。"""
    cells = VGroup()
    for i in range(rows):
        for j in range(cols):
            if heat:
                t = 1.0 - ((i - 0.5) ** 2 + (j - 0.5) ** 2) ** 0.5 / 4.2
                col = _heat_color(float(np.clip(0.2 + 0.75 * t, 0, 1)))
                op = 1.0
            else:
                col = ManimColor("#2a3548")
                op = 0.75
            sq = Square(
                side_length=0.32,
                stroke_width=1.0,
                stroke_color=C_PANEL_EDGE,
                fill_color=col,
                fill_opacity=op,
            )
            sq.move_to(RIGHT * j * 0.36 + DOWN * i * 0.36)
            cells.add(sq)
    cells.move_to(ORIGIN)
    return cells


def _pipeline_stations() -> VGroup:
    """编译装配线：原料 → 烘焙 → 落盘 → 就绪（可视化优先）。"""

    def _station(title: str, accent: str, body: Mobject) -> VGroup:
        card = RoundedRectangle(
            width=2.9,
            height=3.4,
            corner_radius=0.14,
            fill_color=C_PANEL,
            fill_opacity=0.96,
            stroke_color=accent,
            stroke_width=1.8,
        )
        tag = Text(title, font=UI_FONT, font_size=18, color=accent)
        tag.next_to(card.get_top(), DOWN, buff=0.18)
        accent_bar = Line(LEFT * 0.55, RIGHT * 0.55, stroke_color=accent, stroke_width=2.0)
        accent_bar.next_to(tag, DOWN, buff=0.08)
        # 正文上移，给底部「令牌通道」留空，避免移动点压住网格
        body.move_to(card.get_center() + UP * 0.05)
        if body.width > 2.3:
            body.scale_to_fit_width(2.3)
            body.move_to(card.get_center() + UP * 0.05)
        return VGroup(card, tag, accent_bar, body)

    raw = _mini_grid(heat=False)
    baked = _mini_grid(heat=True)
    bomb = Dot(baked.get_corner(UL) + DR * 0.15, radius=0.06, color=C_HOT)
    baked_g = VGroup(baked, bomb)

    disk = RoundedRectangle(
        width=1.7,
        height=1.9,
        corner_radius=0.1,
        fill_color="#121a28",
        stroke_color=C_SAVE,
        stroke_width=2.0,
    )
    row_a = RoundedRectangle(width=1.35, height=0.32, corner_radius=0.06, fill_color=C_SAVE, fill_opacity=0.35, stroke_width=0)
    row_d = RoundedRectangle(width=1.35, height=0.32, corner_radius=0.06, fill_color=C_HOT, fill_opacity=0.35, stroke_width=0)
    la = Text("arrival", font=CODE_FONT, font_size=14, color=C_SAVE)
    ld = Text("damage", font=CODE_FONT, font_size=14, color=C_HOT)
    la.move_to(row_a)
    ld.move_to(row_d)
    rows = VGroup(VGroup(row_a, la), VGroup(row_d, ld)).arrange(DOWN, buff=0.18)
    rows.move_to(disk)
    disk_g = VGroup(disk, rows)

    table = _icon_table(C_GOOD).scale(1.6)
    o1 = Text("O(1)", font=CODE_FONT, font_size=22, color=C_GOOD)
    ready = VGroup(table, o1).arrange(DOWN, buff=0.2)

    stations = VGroup(
        _station("原料地图", C_SUB, raw),
        _station("编译烘焙", C_BAKE, baked_g),
        _station("落盘答卷", C_SAVE, disk_g),
        _station("运行就绪", C_GOOD, ready),
    ).arrange(RIGHT, buff=0.55)
    stations.raw = stations[0]  # type: ignore[attr-defined]
    stations.baked = stations[1]  # type: ignore[attr-defined]
    stations.disk = stations[2]  # type: ignore[attr-defined]
    stations.ready = stations[3]  # type: ignore[attr-defined]
    stations.disk_rows = rows  # type: ignore[attr-defined]
    return stations


def _runtime_hud(arrival_s: float, dmg: int) -> VGroup:
    """运行时右侧 HUD：两个待填槽位 + 血条。"""
    card = RoundedRectangle(
        width=3.6,
        height=4.2,
        corner_radius=0.14,
        fill_color=C_PANEL,
        fill_opacity=0.96,
        stroke_color=C_RUNTIME,
        stroke_width=1.6,
    )
    title = Text("查表结果", font=UI_FONT, font_size=18, color=C_RUNTIME)
    title.next_to(card.get_top(), DOWN, buff=0.22)

    def _slot(label: str, accent: str) -> VGroup:
        box = RoundedRectangle(
            width=2.9,
            height=0.85,
            corner_radius=0.1,
            fill_color="#121a28",
            stroke_color=accent,
            stroke_width=1.4,
        )
        lab = Text(label, font=UI_FONT, font_size=14, color=C_MUTED)
        lab.next_to(box.get_top(), DOWN, buff=0.08).align_to(box.get_left(), LEFT).shift(RIGHT * 0.16)
        return VGroup(box, lab)

    slot_a = _slot("到达", C_SAVE)
    slot_d = _slot("伤害", C_HOT)
    slots = VGroup(slot_a, slot_d).arrange(DOWN, buff=0.22)
    slots.next_to(title, DOWN, buff=0.28)

    hp_track = RoundedRectangle(
        width=2.9,
        height=0.36,
        corner_radius=0.08,
        fill_color="#151c28",
        stroke_color=C_PANEL_EDGE,
        stroke_width=1.2,
    )
    hp_fill = RoundedRectangle(
        width=2.9 * 0.84,
        height=0.28,
        corner_radius=0.06,
        fill_color=C_GOOD,
        fill_opacity=0.95,
        stroke_width=0,
    )
    hp_fill.move_to(hp_track.get_left() + RIGHT * 0.04, aligned_edge=LEFT)
    hp_lbl = Text("HP", font=CODE_FONT, font_size=14, color=C_SUB)
    hp_block = VGroup(hp_lbl, hp_track, hp_fill)
    hp_lbl.next_to(hp_track, UP, buff=0.1).align_to(hp_track, LEFT)
    hp_block.next_to(slots, DOWN, buff=0.4)

    # 待飞入的数值（初始藏在槽外）
    val_a = Text(f"{arrival_s:.2f}s", font=CODE_FONT, font_size=26, color=C_SAVE)
    val_d = Text(f"-{dmg}", font=CODE_FONT, font_size=26, color=C_HOT)
    val_a.move_to(slot_a[0].get_center() + DOWN * 0.08)
    val_d.move_to(slot_d[0].get_center() + DOWN * 0.08)
    val_a.set_opacity(0)
    val_d.set_opacity(0)

    grp = VGroup(card, title, slots, hp_lbl, hp_track, hp_fill, val_a, val_d)
    grp.slot_a = slot_a  # type: ignore[attr-defined]
    grp.slot_d = slot_d  # type: ignore[attr-defined]
    grp.val_a = val_a  # type: ignore[attr-defined]
    grp.val_d = val_d  # type: ignore[attr-defined]
    grp.hp_fill = hp_fill  # type: ignore[attr-defined]
    grp.hp_track = hp_track  # type: ignore[attr-defined]
    return grp


def _formula_block() -> VGroup:
    arr = VGroup(
        Text("arrival", font=CODE_FONT, font_size=18, color=C_SAVE),
        Text("=", font=CODE_FONT, font_size=18, color=C_MUTED),
        Text(f"path_dist / {WAVE_SPEED_M_S}", font=CODE_FONT, font_size=18, color=C_TITLE),
    ).arrange(RIGHT, buff=0.1)
    dmg = VGroup(
        Text("damage", font=CODE_FONT, font_size=18, color=C_BAD),
        Text("=", font=CODE_FONT, font_size=18, color=C_MUTED),
        Text("Falloff(d)", font=CODE_FONT, font_size=18, color=C_TITLE),
    ).arrange(RIGHT, buff=0.1)
    return VGroup(arr, dmg).arrange(DOWN, buff=0.35, aligned_edge=LEFT)


def _lookup_visual(probe: tuple[int, int], arrival_s: float, dmg: int) -> VGroup:
    """O(1) 查表可视化，少文字。"""
    box = RoundedRectangle(
        width=3.5,
        height=2.4,
        corner_radius=0.12,
        fill_color=C_PANEL,
        fill_opacity=0.95,
        stroke_color=C_GOOD,
        stroke_width=1.6,
    )
    title = Text("O(1)", font=CODE_FONT, font_size=28, color=C_GOOD)
    cell = Text(f"[{probe[0]},{probe[1]}]", font=CODE_FONT, font_size=16, color=C_SUB)
    a = Text(f"{arrival_s:.2f}s", font=CODE_FONT, font_size=22, color=C_SAVE)
    d = Text(f"-{dmg}", font=CODE_FONT, font_size=22, color=C_HOT)
    inner = VGroup(title, cell, a, d).arrange(DOWN, buff=0.16)
    inner.move_to(box)
    if inner.width > box.width - 0.4:
        inner.scale_to_fit_width(box.width - 0.4)
        inner.move_to(box)
    return VGroup(box, inner)


def _teach_world(p: np.ndarray) -> np.ndarray:
    """教学坐标 → 左侧画布坐标（不 scale Group）。"""
    return TEACH_SCALE * np.asarray(p, dtype=float) + TEACH_SHIFT


def _fit_teach_vmob(m: Mobject, z: int = Z_MAP) -> Mobject:
    m.scale(TEACH_SCALE, about_point=ORIGIN).shift(TEACH_SHIFT)
    m.set_z_index(z)
    return m


def _fit_teach_grid(grid: DamageGrid) -> DamageGrid:
    """逐点变换，禁止对 DamageGrid 调用 Group.scale。"""
    for i in range(grid.ny):
        for j in range(grid.nx):
            cell = grid.cells[i][j]
            cell.move_to(_teach_world(grid.points[i, j]))
            cell.scale(TEACH_SCALE)
    grid.set_z_index(Z_FIELD)
    return grid


def _teach_right_panel(panel: Mobject, y: float = 0.15) -> Mobject:
    panel.move_to([TEACH_PANEL_X, y, 0])
    if panel.get_right()[0] > FRAME_RIGHT_X:
        panel.shift(LEFT * (panel.get_right()[0] - FRAME_RIGHT_X + 0.1))
    if panel.get_top()[1] > 2.85:
        panel.shift(DOWN * (panel.get_top()[1] - 2.85))
    if panel.get_bottom()[1] < FRAME_BOTTOM_Y + 0.15:
        panel.shift(UP * (FRAME_BOTTOM_Y + 0.15 - panel.get_bottom()[1]))
    panel.set_z_index(Z_TEACH_PANEL)
    return panel


class PrebakeAlgorithmScene(Scene):
    """标题卡 → 动机 → 伤害场教学桥 → CS2 答卷/管线/运行。"""

    def _fade_alive(self, *mobs, rt: float = 0.45) -> None:
        """FadeOut 并强制 remove。DamageGrid 等 Group 不可整体 FadeOut（会触发 scale 崩）。"""
        to_fade: list[Mobject] = []
        seen: set[int] = set()

        def _is_plain_group(m: Mobject) -> bool:
            return isinstance(m, Group) and not isinstance(m, VGroup)

        def _collect(m: Mobject | None) -> None:
            if m is None or id(m) in seen:
                return
            seen.add(id(m))
            if _is_plain_group(m):
                # 点阵 Group：直接对其子 Dot 做 FadeOut，勿对 Group 本身 FadeOut
                for sub in list(getattr(m, "submobjects", []) or []):
                    if id(sub) not in seen:
                        seen.add(id(sub))
                        to_fade.append(sub)
                return
            if m in self.mobjects:
                to_fade.append(m)
                return
            for sub in getattr(m, "submobjects", []) or []:
                _collect(sub)

        for mob in mobs:
            _collect(mob)
        if to_fade:
            self.play(*[FadeOut(m) for m in to_fade], run_time=rt, rate_func=EASE)
        for mob in mobs:
            if mob is None:
                continue
            self.remove(mob)
            for sub in list(getattr(mob, "submobjects", []) or []):
                self.remove(sub)

    def _play_bridge(self, text: str, accent: str = C_SUB) -> None:
        """章节间一句话衔接，保持故事线不断。"""
        tip = Text(text, font=UI_FONT, font_size=22, color=accent)
        tip.move_to(ORIGIN + UP * 0.1)
        rule = Line(LEFT * 1.1, RIGHT * 1.1, stroke_color=accent, stroke_width=1.8)
        rule.set_stroke(opacity=0.75)
        rule.next_to(tip, DOWN, buff=0.16)
        g = VGroup(tip, rule)
        self.play(FadeIn(g, shift=UP * 0.08), run_time=0.4, rate_func=EASE)
        self.wait(0.7)
        self.play(FadeOut(g, shift=DOWN * 0.06), run_time=0.35, rate_func=EASE)

    def _act_teach_model(self, set_header) -> None:
        """教学桥：地图 → 衰减 → 遮挡烘焙 → 采样 → 血条（可视化优先）。"""
        e = np.array([-2.4, 0.55, 0.0])
        walls = make_demo_walls()
        pts, x_min, x_max, y_min, y_max = make_grid_points()
        field_dist = bake_distance_only_field(pts, e, RADIUS, D_MAX)
        field = bake_damage_field(pts, e, RADIUS, D_MAX, walls)
        pa = np.array([0.35, 1.55, 0.0])
        pb = np.array([0.45, 1.15, 0.0])
        pc = np.array([-1.55, 0.9, 0.0])
        e_s, pa_s, pb_s, pc_s = _teach_world(e), _teach_world(pa), _teach_world(pb), _teach_world(pc)

        # ── 3a 地图 ──────────────────────────────────────────────
        set_header("", "伤害场：教学地图", C_BLAST)
        frame = _fit_teach_vmob(map_frame(), Z_MAP)
        src = ExplosionSource(e, RADIUS)
        _fit_teach_vmob(src, Z_MARKERS)
        wall_mobs = VGroup(*[_fit_teach_vmob(w.as_rect(), Z_WALL) for w in walls])
        player_a = PlayerMarker(pa, "A", C_PLAYER_A)
        player_b = PlayerMarker(pb, "B", C_PLAYER_B)
        player_c = PlayerMarker(pc, "C", C_PLAYER_C)
        for p in (player_a, player_b, player_c):
            _fit_teach_vmob(p, Z_MARKERS)

        # 整组入场，保证父级在场景中，便于整组清场
        self.play(FadeIn(frame), FadeIn(wall_mobs), run_time=0.65, rate_func=EASE)
        self.play(FadeIn(src), run_time=0.5, rate_func=EASE)
        ring = Circle(radius=0.12, stroke_color=C_BLAST, stroke_width=2).move_to(e_s)
        self.play(ring.animate.set_width(2.2 * TEACH_SCALE).set_stroke(opacity=0), run_time=1.0, rate_func=EASE)
        self.remove(ring)
        self.play(FadeIn(player_a), FadeIn(player_b), FadeIn(player_c), run_time=0.55, rate_func=EASE)
        self.wait(HOLD)

        # ── 3b 距离 + 二次衰减 ────────────────────────────────────
        set_header("", "距离衰减", C_BLAST)
        self.play(FadeOut(player_b), FadeOut(player_c), run_time=0.4, rate_func=EASE)
        line = DashedLine(e_s, pa_s, stroke_color=C_BLAST_GLOW, stroke_width=2.2)
        line.set_z_index(Z_MARKERS - 1)
        d_lbl = fm("d = |p − e|", font_size=22, color=C_TITLE)
        d_lbl.next_to(line, UP, buff=0.08).set_z_index(Z_TEACH_PANEL)
        self.play(Create(line), FadeIn(d_lbl), run_time=0.7, rate_func=EASE)
        self.wait(BEAT)

        R_ring = Circle(radius=0.04, stroke_color=C_BLAST, stroke_width=2).move_to(e_s)
        R_ring.set_z_index(Z_MARKERS - 2)
        self.play(R_ring.animate.set_width(2 * RADIUS * TEACH_SCALE), run_time=0.9, rate_func=EASE)

        axes = Axes(
            x_range=[0, 1, 0.25],
            y_range=[0, 1.05, 0.25],
            x_length=3.4,
            y_length=2.3,
            tips=False,
            axis_config={"stroke_color": C_MUTED, "stroke_width": 1.4},
        )
        _teach_right_panel(axes, y=0.55)
        x_l = Text("u = d / R", font=CODE_FONT, font_size=14, color=C_SUB).next_to(axes.x_axis, DOWN, buff=0.12)
        y_l = Text("伤害比", font=UI_FONT, font_size=13, color=C_SUB).next_to(axes.y_axis, LEFT, buff=0.08)
        x_l.set_z_index(Z_TEACH_PANEL)
        y_l.set_z_index(Z_TEACH_PANEL)
        linear_curve = axes.plot(lambda u: 1 - u, x_range=[0, 1], color=C_MUTED)
        quad = axes.plot(lambda u: (1 - u) ** 2, x_range=[0, 1], color=C_BLAST)
        linear_curve.set_z_index(Z_TEACH_PANEL)
        quad.set_z_index(Z_TEACH_PANEL)

        self.play(FadeOut(d_lbl), Create(axes), FadeIn(x_l), FadeIn(y_l), run_time=0.65, rate_func=EASE)
        self.play(Create(linear_curve), run_time=0.6, rate_func=EASE)
        self.wait(0.35)
        self.play(Create(quad), linear_curve.animate.set_stroke(opacity=0.3), run_time=0.75, rate_func=EASE)
        q_tag = fm("(1 − u)²", font_size=18, color=C_BLAST).next_to(axes.c2p(0.5, 0.3), UR, buff=0.04)
        q_tag.set_z_index(Z_TEACH_PANEL)
        atten = _formula_damage()
        atten.scale(0.85)
        _teach_right_panel(atten, y=-1.55)
        self.play(FadeIn(q_tag), FadeIn(atten), run_time=0.55, rate_func=EASE)
        self.wait(HOLD_L)
        self._fade_alive(line, R_ring, axes, x_l, y_l, linear_curve, quad, q_tag, atten, player_a, rt=0.5)

        # ── 3c 径向场 → 遮挡 ─────────────────────────────────────
        set_header("", "烘焙场 + 遮挡", C_BAKE)
        self.play(FadeIn(player_a), FadeIn(player_b), FadeIn(player_c), run_time=0.45, rate_func=EASE)
        grid = DamageGrid(pts)
        _fit_teach_grid(grid)
        self.add(grid)
        order = sorted(
            [(i, j) for i in range(GRID_NY) for j in range(GRID_NX)],
            key=lambda ij: float(np.linalg.norm(pts[ij[0], ij[1], :2] - e[:2])),
        )
        for k in range(0, len(order), 10):
            for i, j in order[k : k + 10]:
                grid.set_cell(i, j, field_dist[i, j])
            self.wait(0.07)
        self.wait(BEAT)

        # 材质：用色块可视化，少文字
        mat_chips = VGroup(
            VGroup(
                Square(0.28, fill_color="#2a3548", fill_opacity=1, stroke_width=0),
                Text("1.0", font=CODE_FONT, font_size=14, color=C_TITLE),
            ).arrange(RIGHT, buff=0.1),
            VGroup(
                Square(0.28, fill_color="#a67c52", fill_opacity=1, stroke_width=0),
                Text("0.45", font=CODE_FONT, font_size=14, color=C_TITLE),
            ).arrange(RIGHT, buff=0.1),
            VGroup(
                Square(0.28, fill_color="#5a6578", fill_opacity=1, stroke_width=0),
                Text("0.0", font=CODE_FONT, font_size=14, color=C_TITLE),
            ).arrange(RIGHT, buff=0.1),
        ).arrange(DOWN, buff=0.18, aligned_edge=LEFT)
        mat_box = RoundedRectangle(
            width=3.4,
            height=2.2,
            corner_radius=0.12,
            fill_color=C_PANEL,
            fill_opacity=0.95,
            stroke_color=C_PANEL_EDGE,
        )
        mat_title = Text("V 透过率", font=UI_FONT, font_size=16, color=C_ACCENT)
        mat_inner = VGroup(mat_title, mat_chips).arrange(DOWN, buff=0.2, aligned_edge=LEFT)
        mat_inner.move_to(mat_box)
        panel_vis = VGroup(mat_box, mat_inner)
        _teach_right_panel(panel_vis, y=0.85)
        full_eq = _formula_full_damage()
        full_eq.scale(0.9)
        _teach_right_panel(full_eq, y=-1.35)
        self.play(FadeIn(panel_vis), FadeIn(full_eq), run_time=0.55, rate_func=EASE)

        va = visibility_factor(e, pa, walls)
        vb = visibility_factor(e, pb, walls)
        vc = visibility_factor(e, pc, walls)
        wall0 = walls[0]
        stop = _teach_world(np.array([wall0.x1, float(pc[1]), 0.0]))
        ra = Line(e_s, pa_s, stroke_color=C_PLAYER_A, stroke_width=2.2).set_z_index(Z_MARKERS)
        rb = Line(e_s, pb_s, stroke_color=C_PLAYER_B, stroke_width=2.2).set_z_index(Z_MARKERS)
        rc = Line(e_s, stop, stroke_color=C_PLAYER_C, stroke_width=2.2).set_z_index(Z_MARKERS)
        flash = Dot(stop, radius=0.06, color=C_WARN).set_z_index(Z_MARKERS + 1)

        self.play(Create(ra), run_time=0.45, rate_func=EASE)
        ta = fm(f"V = {va:.2f}", font_size=16, color=C_PLAYER_A).next_to(player_a, RIGHT, buff=0.06)
        ta.set_z_index(Z_TEACH_PANEL)
        self.play(FadeIn(ta), run_time=0.3)
        self.wait(0.35)
        self.play(Create(rb), run_time=0.45, rate_func=EASE)
        tb = fm(f"V = {vb:.2f}", font_size=16, color=C_PLAYER_B).next_to(player_b, DOWN, buff=0.06)
        tb.set_z_index(Z_TEACH_PANEL)
        self.play(FadeIn(tb), rb.animate.set_stroke(opacity=0.5), run_time=0.4)
        self.wait(0.35)
        self.play(Create(rc), FadeIn(flash), run_time=0.5, rate_func=EASE)
        tc = fm(f"V = {vc:.2f}", font_size=16, color=C_PLAYER_C).next_to(player_c, LEFT, buff=0.06)
        tc.set_z_index(Z_TEACH_PANEL)
        self.play(FadeIn(tc), run_time=0.3)
        self.wait(BEAT)

        for k in range(0, len(order), 8):
            for i, j in order[k : k + 8]:
                grid.set_cell(i, j, field[i, j])
            self.wait(0.055)

        da = compute_damage(e, pa, RADIUS, D_MAX, walls)
        db = compute_damage(e, pb, RADIUS, D_MAX, walls)
        dc = compute_damage(e, pc, RADIUS, D_MAX, walls)
        dmg_mobs = VGroup()
        for player, dmg, col in ((player_a, da, C_PLAYER_A), (player_b, db, C_PLAYER_B), (player_c, dc, C_PLAYER_C)):
            ring_p = Circle(radius=0.28 * TEACH_SCALE + 0.08, stroke_color=col, stroke_width=2.2, fill_opacity=0)
            ring_p.move_to(player.get_center()).set_z_index(Z_MARKERS + 1)
            num = Text(f"{dmg:.0f}", font=CODE_FONT, font_size=15, color=col)
            num.move_to(player.get_center()).set_z_index(Z_MARKERS + 2)
            dmg_mobs.add(ring_p, num)
        self.play(FadeIn(dmg_mobs), run_time=0.55, rate_func=EASE)
        self.wait(HOLD_L)

        clear_occ = [
            ra, rb, rc, flash, ta, tb, tc, panel_vis, full_eq, dmg_mobs,
            player_a, player_b, player_c, src, wall_mobs, frame, grid,
        ]
        self._fade_alive(*clear_occ, rt=0.55)

        # ── 3d 运行时采样 ────────────────────────────────────────
        set_header("", "运行时采样", C_RUNTIME)
        frame2 = _fit_teach_vmob(map_frame(), Z_MAP)
        grid2 = DamageGrid(pts, field)
        _fit_teach_grid(grid2)
        self.add(grid2)
        src2 = ExplosionSource(e, RADIUS)
        _fit_teach_vmob(src2, Z_MARKERS)
        walls2 = VGroup(*[_fit_teach_vmob(w.as_rect(), Z_WALL) for w in walls])
        # 路径选在爆心左侧开放区，伤害变化明显，才能看出 NN 阶梯 vs 双线性平滑
        world_corners = [
            np.array([-3.5, 1.8, 0.0]),
            np.array([-3.2, 0.2, 0.0]),
            np.array([-2.6, -0.5, 0.0]),
            np.array([-2.0, 0.2, 0.0]),
            np.array([-2.5, 1.2, 0.0]),
            np.array([-3.0, 1.5, 0.0]),
        ]
        player = PlayerMarker(world_corners[0].copy(), "P", C_ACCENT)
        _fit_teach_vmob(player, Z_MARKERS)
        map_layer = VGroup(frame2, walls2, src2)
        self.play(FadeIn(map_layer), FadeIn(player), run_time=0.6, rate_func=EASE)

        path = VMobject().set_points_as_corners([_teach_world(p) for p in world_corners])
        samples = np.linspace(0, 1, 28)
        world_path = VMobject().set_points_as_corners(world_corners)
        nn_vals, bi_vals = [], []
        for t in samples:
            wp = world_path.point_from_proportion(t)
            nn_vals.append(float(nearest_sample(field, wp[0], wp[1], x_min, x_max, y_min, y_max)))
            bi_vals.append(float(bilinear_sample(field, wp[0], wp[1], x_min, x_max, y_min, y_max)[0]))

        axes2 = Axes(
            x_range=[0, 1, 0.25],
            y_range=[0, 1.05, 0.25],
            x_length=3.3,
            y_length=2.1,
            tips=False,
            axis_config={"stroke_color": C_MUTED},
        )
        _teach_right_panel(axes2, y=0.15)
        x_lab = Text("路径进度", font=UI_FONT, font_size=12, color=C_SUB)
        y_lab = Text("伤害", font=UI_FONT, font_size=12, color=C_SUB)
        x_lab.next_to(axes2.x_axis, DOWN, buff=0.12).set_z_index(Z_TEACH_PANEL)
        y_lab.next_to(axes2.y_axis, LEFT, buff=0.08).set_z_index(Z_TEACH_PANEL)
        nn_n = [v / D_MAX for v in nn_vals]
        bi_n = [v / D_MAX for v in bi_vals]
        nn_pts = [axes2.c2p(float(samples[i]), float(nn_n[i])) for i in range(len(samples))]
        bi_pts = [axes2.c2p(float(samples[i]), float(bi_n[i])) for i in range(len(samples))]
        progress = ValueTracker(0.0)

        def _partial_curve(pts: list, color: str, t: float) -> VMobject:
            n = len(pts)
            k = max(2, int(np.clip(t, 0, 1) * (n - 1)) + 1)
            return VMobject(stroke_color=color, stroke_width=3.0).set_points_as_corners(pts[:k])

        nn_live = always_redraw(
            lambda: _partial_curve(nn_pts, C_MUTED, progress.get_value()).set_z_index(Z_TEACH_PANEL)
        )
        tip = always_redraw(
            lambda: Dot(
                axes2.c2p(
                    float(progress.get_value()),
                    float(np.interp(progress.get_value(), samples, nn_n)),
                ),
                radius=0.07,
                color=C_MUTED,
            ).set_z_index(Z_TEACH_PANEL + 1)
        )
        legend = VGroup(
            Text("— 最近邻（阶梯）", font=UI_FONT, font_size=13, color=C_MUTED),
            Text("— 双线性（平滑）", font=UI_FONT, font_size=13, color=C_ACCENT),
        ).arrange(DOWN, buff=0.12, aligned_edge=LEFT)
        _teach_right_panel(legend, y=1.85)

        self.play(FadeIn(legend), Create(axes2), FadeIn(x_lab), FadeIn(y_lab), run_time=0.55, rate_func=EASE)
        self.add(nn_live, tip)
        self.play(
            MoveAlongPath(player, path),
            progress.animate.set_value(1.0),
            run_time=2.8,
            rate_func=rate_functions.linear,
        )
        self.wait(BEAT)
        bi_graph = VMobject(stroke_color=C_ACCENT, stroke_width=3.0).set_points_as_corners(bi_pts)
        bi_graph.set_z_index(Z_TEACH_PANEL + 1)
        self.play(Create(bi_graph), run_time=1.0, rate_func=EASE)
        self.wait(HOLD)

        sample_p = world_corners[3]
        d_sample = bilinear_sample(field, sample_p[0], sample_p[1], x_min, x_max, y_min, y_max)[0]
        self.remove(nn_live, tip)
        self._fade_alive(
            player, map_layer, legend, axes2, x_lab, y_lab, bi_graph, grid2, rt=0.55
        )

        # ── 3e 血条预览（采样 → 扣血 → 公式，左图右算）──────────────
        set_header("", "血条预览：查表即扣血", C_HP_PREVIEW)
        d0 = float(min(d_sample, 70.0) if d_sample > 1 else 37.0)
        hp = HP_START

        # 左：迷你战场 + 采样点
        mini_frame = _fit_teach_vmob(map_frame(), Z_MAP)
        mini_src = ExplosionSource(e, RADIUS)
        _fit_teach_vmob(mini_src, Z_MARKERS)
        mini_walls = VGroup(*[_fit_teach_vmob(w.as_rect(), Z_WALL) for w in walls])
        mini_grid = DamageGrid(pts, field)
        _fit_teach_grid(mini_grid)
        for cell in mini_grid:
            cell.set_opacity(0.55)
        sample_dot = Dot(_teach_world(sample_p), radius=0.09, color=C_HP_PREVIEW)
        sample_dot.set_z_index(Z_MARKERS + 1)
        sample_ring = Circle(radius=0.22, stroke_color=C_HP_PREVIEW, stroke_width=2.0)
        sample_ring.move_to(sample_dot).set_z_index(Z_MARKERS)
        ds_chip = _mixed_text(
            [("D", "code"), ("s", "ui"), (f" = {d0:.0f}", "code")],
            font_size=16,
            color=C_HP_PREVIEW,
            buff=0.04,
        )
        ds_chip.next_to(sample_dot, UP, buff=0.14).set_z_index(Z_TEACH_PANEL)
        left_stage = VGroup(mini_frame, mini_walls, mini_src, sample_ring, sample_dot, ds_chip)
        # DamageGrid 是 Group，单独 add
        left_stage.shift(LEFT * 0.15)

        # 右：血条 + 三态卡片 + 公式
        bar = HealthBar(width=4.6).move_to(RIGHT * 2.85 + UP * 0.55)
        bar.set_z_index(Z_TEACH_PANEL)
        dmg_t = ValueTracker(d0)
        bar.add_updater(lambda _m: bar.update_values(hp, dmg_t.get_value()))

        def _stat_card(title: str, value_m: Mobject, accent: str) -> VGroup:
            box = RoundedRectangle(
                width=1.55,
                height=0.95,
                corner_radius=0.1,
                fill_color=C_PANEL,
                fill_opacity=0.96,
                stroke_color=accent,
                stroke_width=1.5,
            )
            lab = Text(title, font=UI_FONT, font_size=13, color=C_MUTED)
            lab.next_to(box.get_top(), DOWN, buff=0.1)
            value_m.move_to(box.get_center() + DOWN * 0.12)
            value_m.set_z_index(Z_TEACH_PANEL + 1)
            box.set_z_index(Z_TEACH_PANEL)
            lab.set_z_index(Z_TEACH_PANEL + 1)
            return VGroup(box, lab, value_m)

        h_val = Text(f"{hp:.0f}", font=CODE_FONT, font_size=22, color=C_TITLE)
        ds_val = always_redraw(
            lambda: Text(
                f"{dmg_t.get_value():.0f}",
                font=CODE_FONT,
                font_size=22,
                color=C_HP_PREVIEW,
            ).set_z_index(Z_TEACH_PANEL + 1)
        )
        hp_val = always_redraw(
            lambda: Text(
                f"{predicted_health(hp, dmg_t.get_value()):.0f}",
                font=CODE_FONT,
                font_size=22,
                color=C_GOOD if predicted_health(hp, dmg_t.get_value()) > 20 else C_HP_PREVIEW,
            ).set_z_index(Z_TEACH_PANEL + 1)
        )
        # 占位卡片用静态值定位，动态值用 updater 贴位
        card_h = _stat_card("当前 H", h_val, C_SUB)
        card_ds = _stat_card(
            "采样 Ds",
            Text(f"{d0:.0f}", font=CODE_FONT, font_size=22, color=C_HP_PREVIEW),
            C_HP_PREVIEW,
        )
        card_hp = _stat_card(
            "预计 H'",
            Text("14", font=CODE_FONT, font_size=22, color=C_GOOD),
            C_GOOD,
        )
        cards = VGroup(card_h, card_ds, card_hp).arrange(RIGHT, buff=0.18)
        cards.next_to(bar, DOWN, buff=0.35).set_x(bar.get_center()[0])
        ds_val.add_updater(lambda m: m.move_to(card_ds[2].get_center()))
        hp_val.add_updater(lambda m: m.move_to(card_hp[2].get_center()))
        card_ds[2].set_opacity(0)
        card_hp[2].set_opacity(0)

        formula = _formula_health()
        formula.next_to(cards, DOWN, buff=0.32).set_x(bar.get_center()[0])
        formula.set_z_index(Z_TEACH_PANEL)
        hint = Text("采样伤害写入血条 — 查表的最后一跳", font=UI_FONT, font_size=14, color=C_MUTED)
        hint.next_to(formula, DOWN, buff=0.2).set_x(bar.get_center()[0])

        self.add(mini_grid)
        self.play(
            FadeIn(left_stage),
            FadeIn(bar),
            FadeIn(cards),
            FadeIn(ds_val),
            FadeIn(hp_val),
            run_time=0.75,
            rate_func=EASE,
        )
        self.play(FadeIn(formula), FadeIn(hint), run_time=0.5, rate_func=EASE)
        # Ds 从采样点飞入血条
        fly = Text(f"-{d0:.0f}", font=CODE_FONT, font_size=20, color=C_HP_PREVIEW)
        fly.move_to(sample_dot.get_center()).set_z_index(Z_MARKERS + 2)
        self.play(FadeIn(fly, scale=0.8), run_time=0.25)
        self.play(fly.animate.move_to(bar.get_center()), run_time=0.75, rate_func=EASE)
        self.play(FadeOut(fly, scale=1.2), Flash(bar.preview, color=C_HP_PREVIEW), run_time=0.45)
        self.play(bar.preview.animate.set_opacity(0.25), rate_func=there_and_back, run_time=0.9)
        self.wait(BEAT)

        # 高伤 → 致死预警；再降回可存活
        self.play(dmg_t.animate.set_value(88), run_time=1.35, rate_func=EASE)
        self.play(
            Indicate(bar.lethal, color=C_HP_PREVIEW, scale_factor=1.08),
            run_time=0.7,
            rate_func=EASE,
        )
        self.wait(BEAT)
        self.play(dmg_t.animate.set_value(28), run_time=1.1, rate_func=EASE)
        self.wait(HOLD)
        bar.clear_updaters()
        ds_val.clear_updaters()
        hp_val.clear_updaters()
        self._fade_alive(
            left_stage, mini_grid, bar, cards, ds_val, hp_val, formula, hint, rt=0.5
        )

    def construct(self):
        self.camera.background_color = ManimColor(C_BG)
        start, probe = BOMB_IJ, SURVIVOR_IJ
        dist, arrival, damage, order = _build_bake_fields(start)
        finite = dist[np.isfinite(dist)]
        max_d = float(finite.max()) if finite.size else 1.0
        n_cells = int(np.sum(np.isfinite(dist)))
        probe_d = float(dist[probe[0], probe[1]])
        probe_arrival = float(arrival[probe[0], probe[1]])
        probe_dmg = int(damage[probe[0], probe[1]])

        header: Mobject | None = None

        def set_header(step: str, title: str, accent: str = C_TITLE, rt: float = RT_HEADER) -> Mobject:
            nonlocal header
            new = _step_header(step, title, accent)
            if header is None:
                self.play(FadeIn(new, shift=DOWN * 0.06), run_time=rt, rate_func=EASE)
            else:
                self.play(ReplacementTransform(header, new), run_time=rt, rate_func=EASE)
            header = new
            return new

        def fade_swap(old: Mobject | None, new: Mobject, rt: float = RT_SWAP) -> Mobject:
            if old is None:
                self.play(FadeIn(new, shift=UP * 0.06), run_time=rt, rate_func=EASE)
            else:
                self.play(
                    FadeOut(old, shift=DOWN * 0.06),
                    FadeIn(new, shift=UP * 0.06),
                    run_time=rt,
                    rate_func=EASE,
                )
            return new

        # ── A) 标题卡 ────────────────────────────────────────────────
        chrome = play_prebake_title_card(self, hold_tail=0.55)

        # ── B) 动机：每帧工作量对照 ──────────────────────────────────
        cost = _cost_compare_visual().move_to([0, -0.1, 0])
        # 任务块初始隐藏，再逐个弹出，直观表达「工作量」
        for chip in cost.naive.tasks:
            chip.set_opacity(0)
        cost.smart.tasks.set_opacity(0)

        self.play(
            FadeOut(chrome.fade_group, shift=DOWN * 0.1),
            FadeOut(chrome.grid),
            FadeOut(chrome.title),
            FadeOut(chrome.underline),
            run_time=0.7,
            rate_func=EASE,
        )
        self.remove(chrome.grid)

        set_header("", "为什么要预烘焙？", C_HOT)
        self.play(FadeIn(cost, shift=UP * 0.06), run_time=0.65, rate_func=EASE)
        self.play(
            LaggedStart(*[chip.animate.set_opacity(1) for chip in cost.naive.tasks], lag_ratio=0.07),
            run_time=1.5,
            rate_func=EASE,
        )
        self.play(cost.smart.tasks.animate.set_opacity(1), Flash(cost.smart.tasks, color=C_GOOD), run_time=0.7, rate_func=EASE)

        # 耗时条：ValueTracker + 左对齐 updater，避免 stretch 居中漂移
        def _attach_bar_grow(col, tracker: ValueTracker) -> None:
            fill, track, full_w = col.bar_fill, col.bar_track, col.bar_width

            def _upd(_m=None):
                w = max(0.08, full_w * tracker.get_value())
                fill.set_opacity(0.9)
                fill.stretch_to_fit_width(w)
                fill.move_to(track.get_left(), aligned_edge=LEFT)

            fill.add_updater(_upd)
            _upd()

        t_naive, t_smart = ValueTracker(0.02), ValueTracker(0.02)
        _attach_bar_grow(cost.naive, t_naive)
        _attach_bar_grow(cost.smart, t_smart)
        self.play(
            t_naive.animate.set_value(cost.naive.target_value),
            t_smart.animate.set_value(cost.smart.target_value),
            run_time=1.35,
            rate_func=EASE,
        )
        cost.naive.bar_fill.clear_updaters()
        cost.smart.bar_fill.clear_updaters()
        cost.naive.bar_fill.move_to(cost.naive.bar_track.get_left(), aligned_edge=LEFT)
        cost.smart.bar_fill.move_to(cost.smart.bar_track.get_left(), aligned_edge=LEFT)
        self.wait(HOLD_L)

        # ── C) 空间换时间 · 故事线 ────────────────────────────────────
        # 叙事：一次编译写表 → 用空间换时间 → 运行只查下标 → 答卷即答案
        self.play(
            FadeOut(cost, shift=DOWN * 0.06),
            FadeOut(header),
            run_time=0.5,
            rate_func=EASE,
        )
        header = None
        self._play_bridge("所以把搜索预支到编译期", C_ACCENT)
        set_header("", "空间换时间", C_ACCENT)
        trade = _trade_visual()
        trade.scale_to_fit_width(12.0)
        trade.move_to([0, -0.18, 0])

        # Beat 1 — 编译侧登场：全图走一遍
        self.play(FadeIn(trade.left_shell, shift=RIGHT * 0.08), run_time=0.55, rate_func=EASE)
        self.play(
            LaggedStart(
                *[Indicate(c, color=C_BAKE, scale_factor=1.05) for c in list(trade.bake_grid)],
                lag_ratio=0.035,
            ),
            run_time=1.05,
            rate_func=EASE,
        )

        # Beat 2 — 写出两张表，落盘占空间
        self.play(
            FadeIn(trade.arr_strip, shift=UP * 0.12),
            run_time=0.4,
            rate_func=EASE,
        )
        self.play(
            FadeIn(trade.dmg_strip, shift=UP * 0.12),
            run_time=0.4,
            rate_func=EASE,
        )
        self.play(FadeIn(trade.table_col[2], shift=UP * 0.06), run_time=0.35, rate_func=EASE)
        self.wait(0.35)

        # Beat 3 — 交换桥：答卷从左飞向右
        self.play(FadeIn(trade.bridge, scale=0.9), run_time=0.5, rate_func=EASE)
        courier = Dot(trade.arr_strip.get_center(), radius=0.09, color=C_ACCENT)
        courier.set_z_index(Z_MARKERS)
        self.add(courier)
        path = CubicBezier(
            trade.arr_strip.get_right() + RIGHT * 0.05,
            trade.bridge_arrow.get_center() + UP * 0.55,
            trade.bridge_arrow.get_center() + DOWN * 0.15,
            trade.right_shell.get_left() + LEFT * 0.05 + DOWN * 0.2,
        )
        self.play(
            MoveAlongPath(courier, path),
            trade.bridge_arrow.animate.set_stroke(width=4.2),
            run_time=1.05,
            rate_func=EASE,
        )
        self.play(FadeOut(courier, scale=0.4), run_time=0.25, rate_func=EASE)

        # Beat 4 — 运行侧：坐标落格 → O(1) 查表 → 读数
        self.play(FadeIn(trade.right_shell, shift=LEFT * 0.08), run_time=0.5, rate_func=EASE)
        for idx in (5, 9, 10, 6):
            cell = trade.lut[idx]
            self.play(
                trade.cursor.animate.move_to(cell),
                trade.player.animate.move_to(cell.get_center()),
                run_time=0.26,
                rate_func=EASE,
            )
        self.play(
            FadeIn(trade.o1, scale=0.92),
            Flash(trade.o1, color=C_GOOD, line_length=0.2, num_lines=10),
            run_time=0.65,
            rate_func=EASE,
        )
        self.play(
            FadeIn(trade.readout, shift=UP * 0.08),
            FadeIn(trade.skip_tag, shift=UP * 0.04),
            run_time=0.55,
            rate_func=EASE,
        )
        self.wait(0.45)

        # Beat 5 — 收束：答卷里的两张表（只描边高亮，绝不 set_color 整卡）
        self.play(FadeIn(trade.fields, shift=UP * 0.1), run_time=0.7, rate_func=EASE)
        f_arr, f_dmg = trade.fields[1][0], trade.fields[1][1]
        self.play(
            Circumscribe(f_arr, color=C_SAVE, buff=0.06, time_width=0.45),
            Circumscribe(f_dmg, color=C_HOT, buff=0.06, time_width=0.45),
            f_arr.box.animate.set_stroke(width=2.8),
            f_dmg.box.animate.set_stroke(width=2.8),
            run_time=0.85,
            rate_func=EASE,
        )
        self.play(
            f_arr.box.animate.set_stroke(width=2.0),
            f_dmg.box.animate.set_stroke(width=2.0),
            run_time=0.25,
        )
        self.wait(HOLD)
        trade_alive = VGroup(
            trade.left_shell,
            trade.table_col,
            trade.bridge,
            trade.right_shell,
            trade.right_tail,
            trade.fields,
        )

        # ── C2) 爆炸伤害教学桥 ───────────────────────────────────────
        self.play(FadeOut(trade_alive), FadeOut(header), run_time=0.45, rate_func=EASE)
        header = None
        self._play_bridge("先看清伤害场：从爆炸走到血条", C_BLAST)
        self._act_teach_model(set_header)
        self.play(FadeOut(header), run_time=0.35, rate_func=EASE)
        header = None

        # ── D) 地图写答卷 ────────────────────────────────────────────
        self._play_bridge("同一套逻辑，写进 CS2 地图答卷", C_BAKE)
        grid = GridMap2D(start, probe)
        _place_map(grid)
        sheet = _answer_sheet_card(n_cells)
        _fit_panel(sheet, grid)

        set_header("", "编译：写成答卷", C_BAKE)
        self.play(
            FadeIn(grid, shift=RIGHT * 0.1),
            FadeIn(grid.markers),
            FadeIn(sheet, shift=LEFT * 0.1),
            run_time=RT_MAP,
            rate_func=EASE,
        )
        self.wait(HOLD)

        chunk = max(5, len(order) // 12)
        for k in range(0, len(order), chunk):
            layer = order[k : k + chunk]
            anims = [
                grid.tiles[(i, j)].animate.set_fill(_heat_color(0.72), opacity=1) for i, j in layer
            ]
            self.play(LaggedStart(*anims, lag_ratio=0.04), run_time=0.38, rate_func=EASE)
            for i, j in layer:
                _color_cell(grid, dist, max_d, i, j)
        self.wait(HOLD_L)

        ring = SurroundingRectangle(grid.tiles[probe], color=C_GOOD, buff=0.04, stroke_width=2.5)
        detail = _lookup_visual(probe, probe_arrival, probe_dmg)
        _fit_panel(detail, grid)

        self.play(FadeOut(sheet, shift=UP * 0.05), run_time=0.35, rate_func=EASE)
        set_header("", "翻开一格", C_SAVE)
        self.play(Create(ring), FadeIn(detail, shift=LEFT * 0.08), run_time=0.6, rate_func=EASE)
        self.wait(HOLD)

        formulas = _formula_block()
        _fit_panel(formulas, grid)
        self.play(
            FadeOut(detail, shift=LEFT * 0.05),
            FadeIn(formulas, shift=LEFT * 0.08),
            run_time=0.6,
            rate_func=EASE,
        )
        self.wait(HOLD)
        right_panel = formulas

        # ── E) 编译装配线（可视化）──────────────────────────────────
        self.play(
            FadeOut(grid),
            FadeOut(grid.markers),
            FadeOut(ring),
            FadeOut(right_panel),
            FadeOut(header),
            run_time=0.5,
            rate_func=EASE,
        )
        header = None

        set_header("", "编译：一条装配线", C_BAKE)
        stations = _pipeline_stations()
        stations.scale_to_fit_width(12.2)
        stations.move_to([0, -0.15, 0])
        # 令牌走卡片下沿通道，避免压住「原料地图」等网格正文
        def _token_pos(st: Mobject) -> np.ndarray:
            return st.get_center() + DOWN * 1.15

        belts = VGroup()
        for i in range(3):
            a = Arrow(
                stations[i].get_right() + LEFT * 0.05 + DOWN * 1.15,
                stations[i + 1].get_left() + RIGHT * 0.05 + DOWN * 1.15,
                buff=0.08,
                stroke_width=2.4,
                color=C_ACCENT,
                max_tip_length_to_length_ratio=0.18,
            )
            a.set_opacity(0)
            belts.add(a)
        token = Dot(_token_pos(stations.raw), radius=0.1, color=C_BAKE)
        token.set_opacity(0)
        token.set_z_index(Z_MARKERS)

        for st in stations:
            st.set_opacity(0)
        self.add(stations, belts, token)

        self.play(stations.raw.animate.set_opacity(1), run_time=0.5, rate_func=EASE)
        self.wait(0.35)
        self.play(token.animate.set_opacity(1), run_time=0.25)
        self.play(
            belts[0].animate.set_opacity(1),
            token.animate.move_to(_token_pos(stations.baked)),
            stations.baked.animate.set_opacity(1),
            run_time=0.85,
            rate_func=EASE,
        )
        # stations[i] = card, tag, accent_bar, body
        pulse = Circle(radius=0.2, stroke_color=C_BAKE, stroke_width=2).move_to(stations.baked[3].get_center())
        self.play(pulse.animate.set_width(1.6).set_stroke(opacity=0), run_time=0.7, rate_func=EASE)
        self.remove(pulse)
        self.wait(0.3)
        self.play(
            belts[1].animate.set_opacity(1),
            token.animate.move_to(_token_pos(stations.disk)).set_color(C_SAVE),
            stations.disk.animate.set_opacity(1),
            run_time=0.85,
            rate_func=EASE,
        )
        for row in stations.disk_rows:
            row.set_opacity(0.2)
        self.play(
            stations.disk_rows[0].animate.set_opacity(1),
            stations.disk_rows[1].animate.set_opacity(1),
            run_time=0.7,
            rate_func=EASE,
        )
        self.wait(0.35)
        self.play(
            belts[2].animate.set_opacity(1),
            token.animate.move_to(_token_pos(stations.ready)).set_color(C_GOOD),
            stations.ready.animate.set_opacity(1),
            run_time=0.85,
            rate_func=EASE,
        )
        self.play(Flash(stations.ready[3], color=C_GOOD, line_length=0.25, num_lines=10), run_time=0.55)
        self.wait(HOLD_L)

        self.play(
            FadeOut(stations),
            FadeOut(belts),
            FadeOut(token),
            FadeOut(header),
            run_time=0.55,
            rate_func=EASE,
        )
        header = None

        # ── F) 运行：波前命中 → 数值飞入 HUD ────────────────────────
        self._play_bridge("答卷就绪 — 看一次真实命中", C_RUNTIME)
        grid_rt = GridMap2D(start, probe)
        _place_map(grid_rt)
        for (ci, cj), tile in grid_rt.tiles.items():
            tile.set_fill(C_PANEL, opacity=0.35)

        wave_t = ValueTracker(0.0)

        def _wave_updater(_m):
            r = wave_t.get_value()
            for (ci, cj), tile in grid_rt.tiles.items():
                d = dist[ci, cj]
                if not np.isfinite(d) or d > r:
                    tile.set_fill(C_PANEL, opacity=0.35)
                    continue
                t = float(np.clip(1.0 - d / max_d, 0, 1))
                tile.set_fill(_heat_color(0.25 + 0.75 * (1.0 - t)), opacity=1)

        set_header("", "运行：命中即查表", C_RUNTIME)
        hud = _runtime_hud(probe_arrival, probe_dmg)
        _fit_panel(hud, grid_rt)

        self.play(
            FadeIn(grid_rt),
            FadeIn(grid_rt.markers),
            FadeIn(hud, shift=LEFT * 0.08),
            run_time=RT_MAP,
            rate_func=EASE,
        )
        grid_rt.add_updater(_wave_updater)
        self.wait(BEAT)

        self.play(wave_t.animate.set_value(probe_d), run_time=2.6, rate_func=EASE)
        probe_tile = grid_rt.tiles[probe]
        hit_ring = SurroundingRectangle(probe_tile, color=C_GOOD, buff=0.05, stroke_width=2.8)
        hit_ring.set_z_index(Z_MARKERS)
        self.play(Create(hit_ring), Flash(probe_tile, color=C_GOOD), run_time=0.55, rate_func=EASE)

        fly_a = Text(f"{probe_arrival:.2f}s", font=CODE_FONT, font_size=22, color=C_SAVE)
        fly_d = Text(f"-{probe_dmg}", font=CODE_FONT, font_size=22, color=C_HOT)
        fly_a.move_to(probe_tile.get_center()).set_z_index(Z_MARKERS + 3)
        fly_d.move_to(probe_tile.get_center()).set_z_index(Z_MARKERS + 3)
        self.play(FadeIn(fly_a, scale=0.8), FadeIn(fly_d, scale=0.8), run_time=0.35)
        self.play(
            fly_a.animate.move_to(hud.val_a.get_center()),
            fly_d.animate.move_to(hud.val_d.get_center()),
            run_time=0.85,
            rate_func=EASE,
        )
        hud.val_a.set_opacity(1)
        hud.val_d.set_opacity(1)
        self.remove(fly_a, fly_d)
        self.play(
            Indicate(hud.slot_a[0], color=C_SAVE),
            Indicate(hud.slot_d[0], color=C_HOT),
            run_time=0.7,
            rate_func=EASE,
        )
        target_w = max(0.12, hud.hp_track.width * max(0.05, 0.84 - probe_dmg / 255.0 * 0.55))
        self.play(
            hud.hp_fill.animate.stretch_to_fit_width(target_w).set_color(C_HOT),
            run_time=0.9,
            rate_func=EASE,
        )
        hud.hp_fill.move_to(hud.hp_track.get_left() + RIGHT * 0.04, aligned_edge=LEFT)
        self.wait(HOLD_L)

        grid_rt.remove_updater(_wave_updater)
        self.play(
            *[FadeOut(m) for m in [header, grid_rt, grid_rt.markers, hud, hit_ring] if m is not None],
            run_time=0.7,
            rate_func=EASE,
        )

# ── 预烘焙分镜可视化 ────────────────────────────────────────

import numpy as np
from manim import *

from yty_manim.basic_unit.cs2_damage import (
    C_ACCENT,
    C_BG,
    C_BLAST,
    C_BLAST_GLOW,
    C_HP,
    C_HP_PREVIEW,
    C_MUTED,
    C_PANEL,
    C_PANEL_EDGE,
    C_PLAYER_A,
    C_PLAYER_B,
    C_PLAYER_C,
    C_SUB,
    C_TITLE,
    C_WARN,
    CODE_FONT,
    D_MAX,
    GRID_NX,
    GRID_NY,
    HP_START,
    RADIUS,
    UI_FONT,
    DamageGrid,
    ExplosionSource,
    FormulaPanel,
    fm,
    HealthBar,
    PlayerMarker,
    bake_damage_field,
    bake_distance_only_field,
    bilinear_sample,
    caption,
    compute_damage,
    distance_attenuation,
    make_demo_walls,
    make_grid_points,
    map_frame,
    nearest_sample,
    predicted_health,
    visibility_factor,
)

EASE = rate_functions.ease_in_out_cubic

# 节奏：CFG_FAST 试渲压缩；正式片拉长“读图停顿”，动画本身不故意拖慢
CFG_FAST = False
ANIM_T = 0.45 if CFG_FAST else 1.0
HOLD_T = 0.45 if CFG_FAST else 3.6  # 约把总时长拉到 8～10 分钟量级


def _a(base: float) -> float:
    """动画时长。"""
    return base * ANIM_T


def _w(base: float) -> float:
    """停顿 / 旁白阅读时长。"""
    return base * HOLD_T


class ExplosionPrebakeVisualization(MovingCameraScene):
    """预烘焙伤害场 + 运行时采样 + 血条预览 · 完整教学片。"""

    def construct(self):
        self.camera.background_color = ManimColor(C_BG)
        self.e = np.array([-2.4, 0.55, 0.0])
        self.walls = make_demo_walls()
        self.pts, self.x_min, self.x_max, self.y_min, self.y_max = make_grid_points()
        self.field_dist = bake_distance_only_field(self.pts, self.e, RADIUS, D_MAX)
        self.field = bake_damage_field(self.pts, self.e, RADIUS, D_MAX, self.walls)
        self.pa = np.array([0.35, 1.55, 0.0])
        self.pb = np.array([0.45, 1.15, 0.0])
        self.pc = np.array([-1.55, 0.9, 0.0])

        self.intro_problem()
        self.build_map()
        self.explain_distance()
        self.explain_attenuation()
        self.bake_radial_field()
        self.add_occlusion()
        self.bake_occlusion_field()
        self.runtime_sampling()
        self.health_preview()
        self.cache_invalidation()
        self.complexity_comparison()
        self.accuracy_tradeoff()
        self.final_pipeline()

    # ── helpers ───────────────────────────────────────────────────────
    def _cap(self, text: str, hold: float = 1.6):
        c = caption(text)
        self.play(FadeIn(c, shift=UP * 0.05), run_time=_a(0.35), rate_func=EASE)
        self.wait(_w(hold))
        self.play(FadeOut(c), run_time=_a(0.25))
        return c

    def _clear(self, *mobs):
        alive = [m for m in mobs if m is not None and m in self.mobjects]
        if alive:
            self.play(*[FadeOut(m) for m in alive], run_time=_a(0.45), rate_func=EASE)

    # ── 1 问题引入 ────────────────────────────────────────────────────
    def intro_problem(self):
        title = Text("爆炸伤害预烘焙与血条预览", font=UI_FONT, font_size=40, color=C_TITLE)
        title.set_color_by_gradient(C_BLAST, C_BLAST_GLOW, C_ACCENT)
        sub = Text("教学简化模型 · 非特定引擎实装", font=UI_FONT, font_size=18, color=C_MUTED)
        hero = VGroup(title, sub).arrange(DOWN, buff=0.22).move_to(ORIGIN)
        self.play(FadeIn(hero, shift=UP * 0.1), run_time=_a(0.8), rate_func=EASE)
        self.wait(_w(1.2))
        self.play(FadeOut(hero), run_time=_a(0.4))

        # 简化 HUD
        hp_track = RoundedRectangle(width=3.6, height=0.36, corner_radius=0.08, fill_color="#151c28", stroke_color=C_PANEL_EDGE)
        hp_fill = RoundedRectangle(width=3.6 * 0.84, height=0.28, corner_radius=0.06, fill_color=C_HP, stroke_width=0)
        hp_fill.move_to(hp_track.get_left() + RIGHT * 0.04, aligned_edge=LEFT)
        preview = RoundedRectangle(width=3.6 * 0.37, height=0.28, corner_radius=0.05, fill_color=C_HP_PREVIEW, fill_opacity=0.55, stroke_width=0)
        preview.move_to(hp_fill.get_right(), aligned_edge=RIGHT)
        hp_lbl = Text("HP 84", font=CODE_FONT, font_size=22, color=C_TITLE)
        hp_lbl.next_to(hp_track, UP, buff=0.12).align_to(hp_track, LEFT)
        timer = Text("0:03", font=CODE_FONT, font_size=36, color=C_BLAST)
        timer.to_edge(UP, buff=0.5)
        hud = VGroup(hp_track, hp_fill, preview, hp_lbl).move_to(DOWN * 1.8)

        mini = map_frame().scale(0.55).move_to(UP * 0.4)
        bomb = Dot(mini.get_center() + LEFT * 1.2, radius=0.08, color=C_BLAST)
        self.play(FadeIn(mini), FadeIn(bomb), FadeIn(timer), FadeIn(hud), run_time=_a(0.7))
        self.play(preview.animate.set_opacity(0.15), rate_func=there_and_back, run_time=_a(1.2))
        self.wait(_w(0.6))

        q = Text("爆炸尚未发生，系统如何提前显示伤害？", font=UI_FONT, font_size=28, color=C_TITLE)
        q.to_edge(UP, buff=1.1)
        self.play(FadeIn(q), run_time=_a(0.5))
        self.wait(_w(1.0))

        opts = VGroup(
            Text("① 每一帧重新计算？", font=UI_FONT, font_size=22, color=C_HP_PREVIEW),
            Text("② 提前计算地图伤害分布？", font=UI_FONT, font_size=22, color=C_BLAST_GLOW),
            Text("③ 只在关键事件时更新？", font=UI_FONT, font_size=22, color=C_ACCENT),
        ).arrange(DOWN, buff=0.28, aligned_edge=LEFT).move_to(RIGHT * 3.2 + UP * 0.2)

        # ① 拥挤射线
        rays = VGroup(*[
            Line(bomb.get_center(), bomb.get_center() + 1.4 * np.array([np.cos(a), np.sin(a), 0]),
                 stroke_color=C_HP_PREVIEW, stroke_width=1.2, stroke_opacity=0.5)
            for a in np.linspace(0, TAU, 18, endpoint=False)
        ])
        self.play(FadeIn(opts[0]), LaggedStart(*[Create(r) for r in rays], lag_ratio=0.05), run_time=_a(1.0))
        self.wait(_w(0.7))
        self.play(FadeOut(rays), FadeIn(opts[1]), run_time=_a(0.5))

        # ② 热力暗示
        heat_dots = VGroup(*[
            Dot(mini.get_center() + np.array([dx, dy, 0]), radius=0.06,
                color=interpolate_color(ManimColor(C_BLAST), ManimColor("#3a1010"), (dx**2 + dy**2) ** 0.5 / 1.8))
            for dx in np.linspace(-1.3, 1.3, 7) for dy in np.linspace(-0.8, 0.8, 5)
            if (dx**2 + dy**2) ** 0.5 < 1.5
        ])
        self.play(LaggedStart(*[FadeIn(d, scale=0.5) for d in heat_dots], lag_ratio=0.02), run_time=_a(1.1))
        self.wait(_w(0.5))
        self.play(FadeIn(opts[2]), run_time=_a(0.4))
        probe = Dot(mini.get_center() + RIGHT * 0.9 + UP * 0.2, radius=0.07, color=C_ACCENT)
        self.play(FadeIn(probe), probe.animate.shift(LEFT * 0.5 + DOWN * 0.3), run_time=_a(1.0))
        self.wait(_w(0.6))

        merge = Text("预烘焙伤害场 + 运行时快速采样", font=UI_FONT, font_size=24, color=C_ACCENT)
        merge.next_to(opts, DOWN, buff=0.45).align_to(opts, LEFT)
        box = SurroundingRectangle(VGroup(opts[1], opts[2], merge), color=C_ACCENT, buff=0.18, corner_radius=0.1)
        self.play(FadeIn(merge), Create(box), run_time=_a(0.7))
        self._cap("用空间缓存，换掉每帧昂贵的几何计算", hold=1.8)
        self.play(*[FadeOut(m) for m in [mini, bomb, timer, hud, q, opts, heat_dots, probe, merge, box, hp_track, hp_fill, preview, hp_lbl]],
                  run_time=_a(0.55))

    # ── 2 建立地图 ────────────────────────────────────────────────────
    def build_map(self):
        self.frame = map_frame()
        self.src = ExplosionSource(self.e, RADIUS)
        wall_mobs = VGroup(*[w.as_rect() for w in self.walls])
        labels = VGroup()
        for w in self.walls:
            if w.label:
                t = Text(w.label, font=UI_FONT, font_size=12, color=C_SUB)
                t.move_to(w.as_rect().get_center())
                labels.add(t)
        self.player_a = PlayerMarker(self.pa, "A 近·无遮挡", C_PLAYER_A)
        self.player_b = PlayerMarker(self.pb, "B 中·薄板", C_PLAYER_B)
        self.player_c = PlayerMarker(self.pc, "C 近·厚墙后", C_PLAYER_C)
        # 缩短标签
        for p, name in ((self.player_a, "A"), (self.player_b, "B"), (self.player_c, "C")):
            p.remove(p.submobjects[-1])
            tag = Text(name, font=UI_FONT, font_size=18, color=p.body.get_color())
            tag.next_to(p.body, UP, buff=0.08)
            p.add(tag)

        title = Text("简化俯视地图", font=UI_FONT, font_size=26, color=C_TITLE).to_edge(UP, buff=0.3)
        self.play(FadeIn(title), FadeIn(self.frame), run_time=_a(0.5))
        self.play(LaggedStart(*[FadeIn(w) for w in wall_mobs], lag_ratio=0.12), run_time=_a(0.8))
        self.play(FadeIn(labels), FadeIn(self.src), run_time=_a(0.6))
        ring1 = Circle(radius=0.2, stroke_color=C_BLAST, stroke_width=2).move_to(self.e)
        ring2 = Circle(radius=0.2, stroke_color=C_BLAST_GLOW, stroke_width=1.5).move_to(self.e)
        self.play(
            ring1.animate.set_width(2.4).set_stroke(opacity=0),
            ring2.animate.set_width(1.8).set_stroke(opacity=0),
            run_time=_a(1.2),
            rate_func=EASE,
        )
        self.remove(ring1, ring2)
        self.play(
            FadeIn(self.player_a), FadeIn(self.player_b), FadeIn(self.player_c),
            run_time=_a(0.7),
        )
        legend = VGroup(
            Text("开放区 / 拐角 / 木板 / 混凝土", font=UI_FONT, font_size=16, color=C_MUTED),
        ).to_edge(DOWN, buff=0.35)
        self.play(FadeIn(legend), run_time=_a(0.4))
        self.wait(_w(1.5))
        self.wall_mobs = wall_mobs
        self.wall_labels = labels
        self.map_title = title
        self.map_legend = legend

    # ── 3 距离 ────────────────────────────────────────────────────────
    def explain_distance(self):
        self.play(FadeOut(self.player_b), FadeOut(self.player_c), FadeOut(self.map_legend), run_time=_a(0.4))
        p_tex = fm(r"\mathbf{p}", font_size=28, color=C_PLAYER_A)
        p_tex.next_to(self.player_a, DR, buff=0.05)
        line = DashedLine(self.e, self.pa, stroke_color=C_BLAST_GLOW, stroke_width=2.5)
        d_lbl = fm(r"d=|\mathbf{p}-\mathbf{e}|", font_size=30, color=C_TITLE)
        d_lbl.next_to(line, UP, buff=0.12)
        self.play(FadeIn(p_tex), Create(line), Write(d_lbl), run_time=_a(0.9))
        self._cap("距离是一切衰减的基础：先量爆心到采样点", hold=1.4)

        corner = np.array([self.pa[0], self.e[1], 0])
        hx = DashedLine(self.e, corner, stroke_color=C_ACCENT, stroke_width=2)
        hy = DashedLine(corner, self.pa, stroke_color=C_PLAYER_A, stroke_width=2)
        dx = fm(r"p_x-e_x", font_size=22, color=C_ACCENT).next_to(hx, DOWN, buff=0.08)
        dy = fm(r"p_y-e_y", font_size=22, color=C_PLAYER_A).next_to(hy, RIGHT, buff=0.08)
        self.play(Create(hx), Create(hy), FadeIn(dx), FadeIn(dy), run_time=_a(0.8))
        formula = fm(
            r"d=\sqrt{(p_x-e_x)^2+(p_y-e_y)^2}",
            font_size=32,
            color=C_TITLE,
        ).to_edge(UP, buff=0.85)
        self.play(ReplacementTransform(d_lbl, formula), FadeOut(self.map_title), run_time=_a(0.7))
        self.wait(_w(1.6))
        self.dist_keep = VGroup(line, hx, hy, dx, dy, p_tex, formula)

    # ── 4 半径与衰减 ──────────────────────────────────────────────────
    def explain_attenuation(self):
        self.play(FadeOut(self.dist_keep), FadeOut(self.player_b), FadeOut(self.player_c), run_time=_a(0.45))
        R_ring = Circle(radius=0.05, stroke_color=C_BLAST, stroke_width=2.5).move_to(self.e)
        R_lbl = fm(r"R", font_size=30, color=C_BLAST).next_to(self.e + RIGHT * RADIUS, UP, buff=0.08)
        self.play(R_ring.animate.set_width(2 * RADIUS), FadeIn(R_lbl), run_time=_a(1.1), rate_func=EASE)
        out = Text("有效范围外：伤害为 0", font=UI_FONT, font_size=18, color=C_MUTED)
        out.to_edge(UP, buff=0.35)
        self.play(FadeIn(out), self.frame.animate.set_opacity(0.35), run_time=_a(0.5))
        self.wait(_w(1.0))

        # 右侧曲线
        axes = Axes(
            x_range=[0, 1, 0.25],
            y_range=[0, 1.05, 0.25],
            x_length=4.0,
            y_length=2.8,
            tips=False,
            axis_config={"stroke_color": C_MUTED, "stroke_width": 1.5},
        ).to_edge(RIGHT, buff=0.35).shift(DOWN * 0.2)
        x_l = Text("u = d/R", font=CODE_FONT, font_size=14, color=C_SUB).next_to(axes.x_axis, DOWN, buff=0.15)
        y_l = Text("伤害比", font=UI_FONT, font_size=14, color=C_SUB).next_to(axes.y_axis, LEFT, buff=0.1)
        linear = axes.plot(lambda u: 1 - u, x_range=[0, 1], color=C_MUTED)
        quad = axes.plot(lambda u: (1 - u) ** 2, x_range=[0, 1], color=C_BLAST)
        self.play(FadeOut(out), Create(axes), FadeIn(x_l), FadeIn(y_l), run_time=_a(0.7))
        self.play(Create(linear), run_time=_a(0.7))
        lin_tag = fm(r"1-u", font_size=24, color=C_MUTED).next_to(axes.c2p(0.7, 0.3), RIGHT)
        self.play(FadeIn(lin_tag), run_time=_a(0.3))
        self.wait(_w(0.8))
        self.play(Create(quad), lin_tag.animate.set_opacity(0.35), linear.animate.set_stroke(opacity=0.35), run_time=_a(0.8))
        q_tag = fm(r"(1-u)^2", font_size=24, color=C_BLAST).next_to(axes.c2p(0.55, 0.25), UR, buff=0.05)
        self.play(FadeIn(q_tag), run_time=_a(0.3))

        # 移动采样点
        tracker = ValueTracker(0.35)
        sample = Dot(color=C_ACCENT, radius=0.08)

        def _upd_sample(m):
            u = tracker.get_value()
            ang = 0.35
            p = self.e + RADIUS * u * np.array([np.cos(ang), np.sin(ang), 0])
            m.move_to(p)

        sample.add_updater(_upd_sample)
        tip = Dot(color=C_BLAST, radius=0.07)

        def _upd_tip(m):
            u = tracker.get_value()
            m.move_to(axes.c2p(u, (1 - u) ** 2))

        tip.add_updater(_upd_tip)
        read = always_redraw(
            lambda: Text(
                f"u={tracker.get_value():.2f}  f={(1-tracker.get_value())**2:.2f}  D={D_MAX*(1-tracker.get_value())**2:.0f}",
                font=CODE_FONT,
                font_size=16,
                color=C_TITLE,
            ).to_edge(UP, buff=0.35)
        )
        self.add(sample, tip, read)
        self.play(tracker.animate.set_value(0.85), run_time=_a(2.2), rate_func=EASE)
        self.play(tracker.animate.set_value(0.15), run_time=_a(1.8), rate_func=EASE)
        formula = fm(r"D_{\mathrm{distance}}=D_{\max}(1-u)^2", font_size=30, color=C_TITLE)
        formula.to_edge(UP, buff=0.9)
        self.play(FadeIn(formula), run_time=_a(0.5))
        self._cap("二次衰减让远处伤害下降更快——这是手感设计，不是物理定律", hold=2.0)
        sample.clear_updaters()
        tip.clear_updaters()
        self.play(
            *[FadeOut(m) for m in [axes, x_l, y_l, linear, quad, lin_tag, q_tag, sample, tip, read, formula, R_ring, R_lbl]],
            self.frame.animate.set_opacity(1),
            run_time=_a(0.55),
        )
        self.add(self.player_b, self.player_c)

    # ── 5 径向场烘焙 ──────────────────────────────────────────────────
    def bake_radial_field(self):
        title = Text("空间伤害场：把连续空间离散成网格", font=UI_FONT, font_size=24, color=C_TITLE)
        title.to_edge(UP, buff=0.3)
        grid = DamageGrid(self.pts)
        self.add(grid)
        self.play(FadeIn(title), run_time=_a(0.45))
        self.wait(_w(0.35))
        self._cap("有限网格中心 = 可存储的采样点", hold=1.3)

        # 单格演示
        i0, j0 = GRID_NY // 2, GRID_NX // 2
        g = self.pts[i0, j0]
        cell_h = Circle(radius=0.22, stroke_color=C_ACCENT, stroke_width=2.5).move_to(g)
        panel = FormulaPanel(
            [
                "d_ij = |g_ij - e|",
                "u = clamp(d/R, 0, 1)",
                "D = D_max * (1-u)^2",
            ],
            title="单格计算",
            width=4.4,
        ).to_edge(RIGHT, buff=0.25).shift(UP * 0.3)
        self.play(FadeIn(cell_h), FadeIn(panel), run_time=_a(0.6))
        val = distance_attenuation(float(np.linalg.norm(g[:2] - self.e[:2])), RADIUS, D_MAX)
        grid.set_cell(i0, j0, val)
        self.wait(_w(1.0))
        self.play(FadeOut(cell_h), FadeOut(panel), run_time=_a(0.35))

        # 按距离排序逐圈上色（直接 set_fill，避免对大量格子做 Create/FadeIn）
        order = sorted(
            [(i, j) for i in range(GRID_NY) for j in range(GRID_NX)],
            key=lambda ij: float(np.linalg.norm(self.pts[ij[0], ij[1], :2] - self.e[:2])),
        )
        chunk = 12
        for k in range(0, len(order), chunk):
            batch = order[k : k + chunk]
            for i, j in batch:
                grid.set_cell(i, j, self.field_dist[i, j])
            self.wait(_w(0.06))
        arr = Text("damage_field[i][j]", font=CODE_FONT, font_size=18, color=C_ACCENT)
        arr.to_edge(DOWN, buff=0.35)
        self.play(FadeIn(arr), run_time=_a(0.4))
        self._cap("可在地图加载、下包或爆炸位置确定后生成——统称预计算思想", hold=2.0)
        self.radial_grid = grid
        self.bake_title = title
        self.bake_arr = arr

    # ── 6 遮挡 ────────────────────────────────────────────────────────
    def add_occlusion(self):
        self.remove(self.radial_grid)
        self.play(FadeOut(self.bake_title), FadeOut(self.bake_arr), run_time=_a(0.35))

        self.frame = map_frame()
        self.src = ExplosionSource(self.e, RADIUS)
        self.wall_mobs = VGroup(*[w.as_rect() for w in self.walls])
        self.player_a = PlayerMarker(self.pa, "A", C_PLAYER_A)
        self.player_b = PlayerMarker(self.pb, "B", C_PLAYER_B)
        self.player_c = PlayerMarker(self.pc, "C", C_PLAYER_C)
        self.play(
            FadeIn(self.frame), FadeIn(self.wall_mobs), FadeIn(self.src),
            FadeIn(self.player_a), FadeIn(self.player_b), FadeIn(self.player_c),
            run_time=_a(0.6),
        )
        title = Text("只有距离还不够：墙体与材质", font=UI_FONT, font_size=24, color=C_TITLE).to_edge(UP, buff=0.3)
        self.play(FadeIn(title), run_time=_a(0.4))

        va = visibility_factor(self.e, self.pa, self.walls)
        vb = visibility_factor(self.e, self.pb, self.walls)
        vc = visibility_factor(self.e, self.pc, self.walls)
        wall0 = self.walls[0]
        stop = np.array([wall0.x1, float(self.pc[1]), 0.0])
        ra = Line(self.e, self.pa, stroke_color=C_PLAYER_A, stroke_width=2.5)
        rb = Line(self.e, self.pb, stroke_color=C_PLAYER_B, stroke_width=2.5)
        rc = Line(self.e, stop, stroke_color=C_PLAYER_C, stroke_width=2.5)
        flash = Dot(stop, radius=0.07, color=C_WARN)

        self.play(Create(ra), run_time=_a(0.5))
        ta = fm(f"V_A={va:.2f}", font_size=26, color=C_PLAYER_A).next_to(self.player_a, RIGHT)
        self.play(FadeIn(ta), run_time=_a(0.3))
        self.play(Create(rb), run_time=_a(0.5))
        tb = fm(f"V_B={vb:.2f}", font_size=26, color=C_PLAYER_B).next_to(self.player_b, DOWN)
        self.play(FadeIn(tb), rb.animate.set_stroke(opacity=0.45), run_time=_a(0.4))
        self.play(Create(rc), FadeIn(flash), run_time=_a(0.55))
        tc = fm(f"V_C={vc:.2f}", font_size=26, color=C_PLAYER_C).next_to(self.player_c, LEFT)
        self.play(FadeIn(tc), run_time=_a(0.3))

        table = FormulaPanel(
            ["开放 1.00", "薄木板 0.45", "砖墙 0.15", "厚混凝土 0.00"],
            title="材质透过（演示）",
            width=3.6,
        ).to_edge(RIGHT, buff=0.3)
        self.play(FadeIn(table), run_time=_a(0.5))
        formula = fm("D = D_max*(1-u)^2 * V(e,p)", font_size=26, color=C_TITLE).next_to(title, DOWN, buff=0.2)
        self.play(FadeIn(formula), run_time=_a(0.5))

        da = compute_damage(self.e, self.pa, RADIUS, D_MAX, self.walls)
        db = compute_damage(self.e, self.pb, RADIUS, D_MAX, self.walls)
        dc = compute_damage(self.e, self.pc, RADIUS, D_MAX, self.walls)
        dmg_labels = VGroup()
        for player, dmg, col in (
            (self.player_a, da, C_PLAYER_A),
            (self.player_b, db, C_PLAYER_B),
            (self.player_c, dc, C_PLAYER_C),
        ):
            ring = Circle(radius=0.32, stroke_color=col, stroke_width=2.5, fill_opacity=0).move_to(player.get_center())
            num = Text(f"{dmg:.0f}", font=CODE_FONT, font_size=16, color=col).move_to(player.get_center())
            dmg_labels.add(ring, num)
            self.play(FadeIn(ring), FadeIn(num), run_time=_a(0.3))
        punch = Text("距离近，不代表伤害一定高", font=UI_FONT, font_size=26, color=C_WARN)
        punch.to_edge(DOWN, buff=0.35)
        self.play(FadeIn(punch), run_time=_a(0.5))
        self.wait(_w(2.0))
        clear = [
            ra, rb, rc, flash, ta, tb, tc, table, formula, title, punch, dmg_labels,
            self.player_a, self.player_b, self.player_c, self.frame, self.src, self.wall_mobs,
        ]
        self.play(*[FadeOut(m) for m in clear], run_time=_a(0.5))

    # ── 7 遮挡烘焙对比 ────────────────────────────────────────────────
    def bake_occlusion_field(self):
        title = Text("加入遮挡后：圆对称 → 地图切割", font=UI_FONT, font_size=24, color=C_TITLE)
        title.to_edge(UP, buff=0.3)
        grid = DamageGrid(self.pts, self.field_dist)
        tag = Text("仅距离衰减", font=UI_FONT, font_size=18, color=C_MUTED).to_edge(DOWN, buff=0.35)
        self.add(grid)
        self.play(FadeIn(title), FadeIn(tag), run_time=_a(0.5))
        self.wait(_w(1.2))
        self.play(FadeOut(tag), run_time=_a(0.25))
        tag2 = Text("距离 + 墙体/材质", font=UI_FONT, font_size=18, color=C_BLAST).to_edge(DOWN, buff=0.35)
        # 逐圈改写为遮挡场
        order = sorted(
            [(i, j) for i in range(GRID_NY) for j in range(GRID_NX)],
            key=lambda ij: float(np.linalg.norm(self.pts[ij[0], ij[1], :2] - self.e[:2])),
        )
        self.play(FadeIn(tag2), run_time=_a(0.3))
        for k in range(0, len(order), 10):
            for i, j in order[k : k + 10]:
                grid.set_cell(i, j, self.field[i, j])
            self.wait(_w(0.07))
        mid = fm("D_distance  ->  D_distance+visibility", font_size=24, color=C_TITLE)
        mid.next_to(title, DOWN, buff=0.18)
        self.play(FadeIn(mid), run_time=_a(0.5))
        self._cap("同心圆被地图几何切成阴影与半影", hold=2.0)
        self.remove(grid)
        self.play(FadeOut(title), FadeOut(tag2), FadeOut(mid), run_time=_a(0.4))

    # ── 8 运行时采样 ──────────────────────────────────────────────────
    def runtime_sampling(self):
        self.frame = map_frame()
        self.src = ExplosionSource(self.e, RADIUS)
        self.wall_mobs = VGroup(*[w.as_rect() for w in self.walls])
        grid = DamageGrid(self.pts, self.field)
        player = PlayerMarker(np.array([1.6, -0.2, 0.0]), "P", C_ACCENT)
        title = Text("运行时：查表，不重算整张图", font=UI_FONT, font_size=24, color=C_TITLE).to_edge(UP, buff=0.28)
        self.add(grid)
        self.play(
            FadeIn(self.frame), FadeIn(self.wall_mobs), FadeIn(self.src),
            FadeIn(player), FadeIn(title),
            run_time=_a(0.7),
        )

        path = VMobject().set_points_as_corners([
            player.get_center(),
            np.array([0.8, 0.6, 0]),
            np.array([-0.3, 1.2, 0]),
            np.array([1.2, 1.4, 0]),
            np.array([2.2, 0.5, 0]),
        ])
        # 最近邻
        nn_vals = []
        bi_vals = []
        samples = np.linspace(0, 1, 24)
        for t in samples:
            p = path.point_from_proportion(t)
            nn_vals.append(nearest_sample(self.field, p[0], p[1], self.x_min, self.x_max, self.y_min, self.y_max))
            bi_vals.append(bilinear_sample(self.field, p[0], p[1], self.x_min, self.x_max, self.y_min, self.y_max)[0])

        axes = Axes(
            x_range=[0, 1, 0.25],
            y_range=[0, 1.05, 0.25],
            x_length=4.2,
            y_length=2.2,
            tips=False,
            axis_config={"stroke_color": C_MUTED},
        ).to_edge(RIGHT, buff=0.2).shift(DOWN * 1.5)
        nn_n = [v / D_MAX for v in nn_vals]
        bi_n = [v / D_MAX for v in bi_vals]
        nn_graph = axes.plot(lambda u: float(np.interp(u, samples, nn_n)), x_range=[0, 1], color=C_MUTED)
        bi_graph = axes.plot(lambda u: float(np.interp(u, samples, bi_n)), x_range=[0, 1], color=C_ACCENT)
        self.play(Create(axes), run_time=_a(0.4))
        self.play(MoveAlongPath(player, path), Create(nn_graph), run_time=_a(3.0), rate_func=linear)
        nn_tag = Text("最近邻：阶梯", font=UI_FONT, font_size=14, color=C_MUTED).next_to(axes, UP, buff=0.08)
        self.play(FadeIn(nn_tag), run_time=_a(0.3))
        self.wait(_w(0.6))

        # 双线性示意
        tip = Text("双线性：四邻域融合", font=UI_FONT, font_size=16, color=C_ACCENT).to_edge(DOWN, buff=0.3)
        self.play(FadeIn(tip), Create(bi_graph), run_time=_a(0.8))
        self.wait(_w(1.2))
        formula = fm(
            r"D=(1-t)[(1-s)D_{00}+sD_{10}]+t[(1-s)D_{01}+sD_{11}]",
            font_size=22,
            color=C_TITLE,
        ).next_to(title, DOWN, buff=0.15)
        self.play(FadeIn(formula), run_time=_a(0.5))
        self._cap("预计算生成数据；运行时只做常数次读写与插值", hold=2.0)
        self.remove(grid)
        self.play(
            *[FadeOut(m) for m in [player, title, axes, nn_graph, bi_graph, nn_tag, tip, formula, self.frame, self.wall_mobs, self.src]],
            run_time=_a(0.5),
        )

    # ── 9 血条预览 ────────────────────────────────────────────────────
    def health_preview(self):
        title = Text("血条红色区 = 预计损失", font=UI_FONT, font_size=26, color=C_TITLE).to_edge(UP, buff=0.35)
        bar = HealthBar(width=5.5).move_to(ORIGIN + UP * 0.4)
        dmg_t = ValueTracker(37)
        hp = HP_START

        def _upd(_m=None):
            bar.update_values(hp, dmg_t.get_value())

        bar.add_updater(lambda m: bar.update_values(hp, dmg_t.get_value()))
        formula = fm("H_after = max(0, H - D_sample)", font_size=28, color=C_TITLE).next_to(bar, DOWN, buff=0.55)
        nums = always_redraw(
            lambda: Text(
                f"预计伤害 {dmg_t.get_value():.0f}  ->  剩余 {predicted_health(hp, dmg_t.get_value()):.0f}",
                font=UI_FONT,
                font_size=20,
                color=C_SUB,
            ).next_to(formula, DOWN, buff=0.3)
        )
        self.play(FadeIn(title), FadeIn(bar), FadeIn(formula), FadeIn(nums), run_time=_a(0.8))
        self.play(bar.preview.animate.set_opacity(0.2), rate_func=there_and_back, run_time=_a(1.4))
        self.wait(_w(1.2))
        self.play(dmg_t.animate.set_value(90), run_time=_a(2.2), rate_func=EASE)
        self.wait(_w(1.5))
        self.play(dmg_t.animate.set_value(20), run_time=_a(1.4), rate_func=EASE)
        self._cap("红色预览区低频闪烁；致死时钳制到 0，不出现负血", hold=1.8)
        bar.clear_updaters()
        self.play(*[FadeOut(m) for m in [title, bar, formula, nums]], run_time=_a(0.45))

    # ── 10 缓存失效 ───────────────────────────────────────────────────
    def cache_invalidation(self):
        steps = ["炸弹位置确定", "生成/选择缓存", "玩家移动", "查询缓存", "更新 HUD", "爆炸结算"]
        nodes = VGroup()
        for s in steps:
            box = RoundedRectangle(width=2.0, height=0.55, corner_radius=0.08, fill_color=C_PANEL, stroke_color=C_PANEL_EDGE)
            t = Text(s, font=UI_FONT, font_size=14, color=C_TITLE).move_to(box)
            nodes.add(VGroup(box, t))
        nodes.arrange(RIGHT, buff=0.22).scale(0.92).move_to(UP * 1.5)
        arrows = VGroup(*[
            Arrow(nodes[i].get_right(), nodes[i + 1].get_left(), buff=0.05, stroke_width=2, color=C_ACCENT, max_tip_length_to_length_ratio=0.2)
            for i in range(len(nodes) - 1)
        ])
        title = Text("事件流与缓存失效", font=UI_FONT, font_size=24, color=C_TITLE).to_edge(UP, buff=0.3)
        self.play(FadeIn(title), LaggedStart(*[FadeIn(n) for n in nodes], lag_ratio=0.12), run_time=_a(1.0))
        self.play(LaggedStart(*[FadeIn(a) for a in arrows], lag_ratio=0.1), run_time=_a(0.8))

        dirty = RoundedRectangle(width=3.2, height=1.6, corner_radius=0.1, fill_color="#2a1a10", stroke_color=C_WARN, stroke_width=2)
        dirty.move_to(DOWN * 0.9)
        warn = Text("缓存与几何不一致", font=UI_FONT, font_size=18, color=C_WARN).move_to(dirty.get_center() + UP * 0.35)
        fix = Text("Ω_dirty 局部重算 / 版本号 / 双缓冲", font=UI_FONT, font_size=16, color=C_SUB).move_to(dirty.get_center() + DOWN * 0.35)
        self.play(FadeIn(dirty), FadeIn(warn), run_time=_a(0.5))
        self.play(FadeIn(fix), run_time=_a(0.4))
        self.wait(_w(2.0))
        self.play(*[FadeOut(m) for m in [title, nodes, arrows, dirty, warn, fix]], run_time=_a(0.45))

    # ── 11 复杂度 ─────────────────────────────────────────────────────
    def complexity_comparison(self):
        left = RoundedRectangle(width=5.6, height=4.2, corner_radius=0.12, fill_color=C_PANEL, stroke_color=C_HP_PREVIEW)
        right = RoundedRectangle(width=5.6, height=4.2, corner_radius=0.12, fill_color=C_PANEL, stroke_color=C_ACCENT)
        left.move_to(LEFT * 3.2)
        right.move_to(RIGHT * 3.2)
        lt = Text("每帧直接计算", font=UI_FONT, font_size=22, color=C_HP_PREVIEW).next_to(left, UP, buff=0.15)
        rt = Text("预计算伤害场", font=UI_FONT, font_size=22, color=C_ACCENT).next_to(right, UP, buff=0.15)
        lbody = VGroup(
            fm(r"O(F\cdot P\cdot K)", font_size=32, color=C_TITLE),
            Text("每帧数百次几何检测", font=UI_FONT, font_size=16, color=C_SUB),
            Text("（示意，非实测）", font=UI_FONT, font_size=14, color=C_MUTED),
        ).arrange(DOWN, buff=0.25).move_to(left)
        rbody = VGroup(
            fm(r"O(N_x N_y K)\ +\ O(P)", font_size=28, color=C_TITLE),
            Text("一次生成，每玩家常数次采样", font=UI_FONT, font_size=16, color=C_SUB),
            Text("（示意，非实测）", font=UI_FONT, font_size=14, color=C_MUTED),
        ).arrange(DOWN, buff=0.25).move_to(right)
        # 左侧忙碌射线
        busy = VGroup(*[
            Line(left.get_center() + LEFT * 0.8, left.get_center() + 1.2 * np.array([np.cos(a), np.sin(a), 0]),
                 stroke_color=C_HP_PREVIEW, stroke_width=1.2, stroke_opacity=0.45)
            for a in np.linspace(0, TAU, 12, endpoint=False)
        ])
        self.play(FadeIn(left), FadeIn(right), FadeIn(lt), FadeIn(rt), run_time=_a(0.5))
        self.play(FadeIn(lbody), FadeIn(rbody), run_time=_a(0.5))
        self.play(LaggedStart(*[Create(r) for r in busy], lag_ratio=0.05), run_time=_a(1.0))
        self.play(FadeOut(busy), run_time=_a(0.3))
        self.wait(_w(2.0))
        self.play(*[FadeOut(m) for m in [left, right, lt, rt, lbody, rbody]], run_time=_a(0.45))

    # ── 12 精度权衡 ───────────────────────────────────────────────────
    def accuracy_tradeoff(self):
        title = Text("精度权衡：网格越密越准，也越贵", font=UI_FONT, font_size=24, color=C_TITLE).to_edge(UP, buff=0.3)
        self.play(FadeIn(title), run_time=_a(0.4))
        cards = VGroup()
        for name, detail, accent in (
            ("低 8x5", "块状明显 · 缓存小", C_MUTED),
            ("中 16x10", "常用折中", C_ACCENT),
            ("高 28x16", "边界更准 · 更贵", C_BLAST),
        ):
            box = RoundedRectangle(width=3.2, height=1.8, corner_radius=0.12, fill_color=C_PANEL, stroke_color=accent, stroke_width=1.6)
            t1 = Text(name, font=UI_FONT, font_size=24, color=accent)
            t2 = Text(detail, font=UI_FONT, font_size=16, color=C_SUB)
            inner = VGroup(t1, t2).arrange(DOWN, buff=0.2).move_to(box)
            cards.add(VGroup(box, inner))
        cards.arrange(RIGHT, buff=0.35).move_to(ORIGIN + DOWN * 0.1)
        self.play(LaggedStart(*[FadeIn(c, shift=UP * 0.08) for c in cards], lag_ratio=0.15), run_time=_a(1.0))
        note = Text("预计算不是免费精确，而是用可控误差换运行效率", font=UI_FONT, font_size=20, color=C_WARN)
        note.to_edge(DOWN, buff=0.4)
        box = SurroundingRectangle(note, color=C_WARN, buff=0.15, corner_radius=0.08)
        self.play(FadeIn(note), Create(box), run_time=_a(0.6))
        self.wait(_w(2.2))
        self.play(FadeOut(title), FadeOut(cards), FadeOut(note), FadeOut(box), run_time=_a(0.45))

    # ── 13 复盘管线 ───────────────────────────────────────────────────
    def final_pipeline(self):
        title = Text("完整数据管线", font=UI_FONT, font_size=26, color=C_TITLE).to_edge(UP, buff=0.28)
        steps = [
            ("e,R,Dmax", "爆炸参数"),
            ("Grid", "空间采样"),
            ("d,u", "距离"),
            ("(1-u)^2", "衰减"),
            ("V", "遮挡"),
            ("Field", "写入缓存"),
            ("Sample", "四点插值"),
            ("A", "护甲修正"),
            ("H_prev", "血条预览"),
        ]
        nodes = VGroup()
        for tex, name in steps:
            box = RoundedRectangle(width=1.35, height=1.05, corner_radius=0.08, fill_color=C_PANEL, stroke_color=C_PANEL_EDGE)
            t1 = Text(tex, font=CODE_FONT, font_size=14, color=C_ACCENT)
            t2 = Text(name, font=UI_FONT, font_size=12, color=C_SUB)
            inner = VGroup(t1, t2).arrange(DOWN, buff=0.08).move_to(box)
            if inner.width > box.width - 0.15:
                inner.scale_to_fit_width(box.width - 0.15)
                inner.move_to(box)
            nodes.add(VGroup(box, inner))
        nodes.arrange(RIGHT, buff=0.1).scale(0.92).move_to(UP * 0.9)
        self.play(FadeIn(title), run_time=_a(0.35))
        for n in nodes:
            self.play(FadeIn(n), run_time=_a(0.2))
            self.wait(_w(0.1))

        big = fm("H_preview = max(0, H - A * Sample(Field, p))", font_size=24, color=C_TITLE).move_to(DOWN * 0.55)
        box = SurroundingRectangle(big, color=C_ACCENT, buff=0.18, corner_radius=0.1)
        self.play(FadeIn(big), Create(box), run_time=_a(0.8))
        self.wait(_w(1.2))

        modules = VGroup(
            Text("爆炸有多强", font=UI_FONT, font_size=20, color=C_BLAST),
            Text("当前位置受多大影响", font=UI_FONT, font_size=20, color=C_ACCENT),
            Text("血条应预览多少损失", font=UI_FONT, font_size=20, color=C_HP_PREVIEW),
        ).arrange(DOWN, buff=0.22).move_to(DOWN * 2.0)
        self.play(LaggedStart(*[FadeIn(m, shift=UP * 0.05) for m in modules], lag_ratio=0.15), run_time=_a(0.9))
        self.wait(_w(1.5))
        self.play(*[FadeOut(m) for m in [title, nodes, big, box, modules]], run_time=_a(0.5))

        end = Text("预烘焙的本质：用空间缓存交换运行时计算。", font=UI_FONT, font_size=28, color=C_TITLE)
        tip = Text("教学模型，不代表任何特定游戏引擎的真实内部实现。", font=UI_FONT, font_size=16, color=C_MUTED)
        VGroup(end, tip).arrange(DOWN, buff=0.28).move_to(ORIGIN)
        self.play(FadeIn(end), run_time=_a(0.7))
        self.play(FadeIn(tip), run_time=_a(0.5))
        self.wait(_w(3.0))
