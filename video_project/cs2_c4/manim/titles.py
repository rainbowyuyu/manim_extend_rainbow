# rainbow_yu — CS2 C4 成片：目录与章节标题卡
"""TOC + 冲击波 / 搜索 / 预烘焙 标题卡。

Usage:
    python -m manim -qh video_project/cs2_c4/manim/titles.py ContentsPageScene
    python -m manim -qh video_project/cs2_c4/manim/titles.py ShockwaveTitleScene
    python -m manim -qh video_project/cs2_c4/manim/titles.py PathfindingTitleScene
    python -m manim -qh video_project/cs2_c4/manim/titles.py PrebakeTitleScene
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from manim import *

from yty_manim.disposition.fonts_and_colors import gradient_dict, text_font

__all__ = (
    "ContentsPageScene",
    "ShockwaveTitleScene",
    "PathfindingTitleScene",
    "PrebakeTitleScene",
    "TitleCardResult",
    "PrebakeTitleCardResult",
    "play_pathfinding_title_card",
    "play_prebake_title_card",
)


# ── 内容总览 ────────────────────────────────────────────────

C_BG = "#07090f"
C_SUB = "#a8b4c8"
C_TITLE = "#f1f5ff"
RAINBOW = gradient_dict["rainbow_color"]
FAV = gradient_dict["favourite"]
ORANGE_PINK = gradient_dict["orange_pink_blue"]

# 四章：主标题 + 一句话介绍
MODULES: tuple[tuple[str, str, str], ...] = (
    ("01", "冲击波算法", "旧球穿墙 vs 路径波前 · 3D 对比演示"),
    ("02", "搜索算法拓展", "欧氏 · BFS · Dijkstra · A* · 贪心"),
    ("03", "预烘焙算法", "编译一次 Dijkstra · 运行时 O(1) 查表"),
    ("04", "分布代码解析", "gameinfo 管线 · vdata · 运行时伪代码"),
)


def _safe_ui_font() -> str:
    try:
        from manim.utils.fonts import get_available_fonts

        available = set(get_available_fonts())
        for name in (*text_font, "Microsoft YaHei", "SimHei", "Noto Sans CJK SC", "Sans"):
            if name in available:
                return name
    except Exception:
        pass
    return "Sans"


UI_FONT = _safe_ui_font()


def _soft_grid() -> VGroup:
    """Lighter / whiter tactical grid."""
    g = VGroup()
    for x in np.arange(-7.2, 7.3, 0.75):
        op = 0.22 if abs(x) < 0.01 else 0.12
        g.add(
            Line(
                [x, -4, 0],
                [x, 4, 0],
                stroke_color="#d8e0ec",
                stroke_width=1.0,
                stroke_opacity=op,
            )
        )
    for y in np.arange(-4.0, 4.1, 0.75):
        op = 0.22 if abs(y) < 0.01 else 0.12
        g.add(
            Line(
                [-7.2, y, 0],
                [7.2, y, 0],
                stroke_color="#d8e0ec",
                stroke_width=1.0,
                stroke_opacity=op,
            )
        )
    return g


def _chapter_row(num: str, title: str, blurb: str, accent) -> VGroup:
    dot = Dot(radius=0.11, color=accent)
    num_t = Text(num, font="Consolas", font_size=24, color=accent)
    title_t = Text(title, font=UI_FONT, font_size=30, color=C_TITLE)
    blurb_t = Text(blurb, font=UI_FONT, font_size=17, color=C_SUB)
    text = VGroup(title_t, blurb_t).arrange(DOWN, buff=0.1, aligned_edge=LEFT)
    if text.width > 10.5:
        text.set_width(10.5)
    row = VGroup(dot, num_t, text).arrange(RIGHT, buff=0.3, aligned_edge=DOWN)
    num_t.align_to(title_t, UP)
    return row


def _shockwave_burst(center, accent):
    rings = VGroup(
        *[
            Circle(
                radius=0.12,
                stroke_color=accent if k % 2 == 0 else FAV[0],
                stroke_width=2.2,
            ).move_to(center)
            for k in range(3)
        ]
    )
    sparks = VGroup()
    for i in range(8):
        ang = i * TAU / 8
        d = Dot(center, radius=0.03, color=accent)
        d.shift_vec = np.array([np.cos(ang), np.sin(ang), 0.0]) * 0.85  # type: ignore[attr-defined]
        sparks.add(d)
    return rings, sparks


class ContentsPageScene(Scene):
    """内容总览：居中入场 → 左上 · 四章各约 3s · 总长约 15s。"""

    def construct(self):
        self.camera.background_color = ManimColor(C_BG)
        grid = _soft_grid()
        self.add(grid)

        # ── 创意入场（OpeningManim + LaggedStart/Flash/Create/GrowFromCenter）──
        # 1) FocusOn → Flash 聚焦中心
        focus = Dot(ORIGIN, radius=0.06, color=FAV[0])
        self.play(FocusOn(focus, opacity=0.35), run_time=0.35)
        self.play(
            Flash(focus, color=FAV[0], line_length=0.4, num_lines=14, flash_radius=0.65),
            run_time=0.4,
        )
        self.remove(focus)

        # 2) 逐字升起（LaggedStart + FadeIn scale）
        chars = VGroup(
            *[
                Text(ch, font=UI_FONT, font_size=56, color=C_TITLE)
                for ch in "内容总览"
            ]
        )
        for i, ch in enumerate(chars):
            ch.set_color(
                interpolate_color(
                    ManimColor(FAV[0]),
                    ManimColor(RAINBOW[5]),
                    i / max(len(chars) - 1, 1),
                )
            )
        chars.arrange(RIGHT, buff=0.12).move_to(ORIGIN)

        self.play(
            LaggedStart(
                *[FadeIn(ch, shift=UP * 0.5, scale=0.45) for ch in chars],
                lag_ratio=0.2,
            ),
            run_time=1.0,
            rate_func=smooth,
        )

        # 3) Create 底线 + 双环外扩（避免零长度 Line 动画崩溃）
        underline = Line(
            chars.get_left() + DOWN * 0.52 + LEFT * 0.06,
            chars.get_right() + DOWN * 0.52 + RIGHT * 0.06,
            stroke_color=FAV[0],
            stroke_width=3.2,
        )
        ring_a = Circle(radius=0.18, stroke_color=FAV[0], stroke_width=1.8, stroke_opacity=0.75).move_to(ORIGIN)
        ring_b = Circle(radius=0.18, stroke_color=RAINBOW[5], stroke_width=1.3, stroke_opacity=0.55).move_to(ORIGIN)

        self.play(
            Create(underline),
            GrowFromCenter(ring_a),
            GrowFromCenter(ring_b),
            run_time=0.5,
            rate_func=smooth,
        )
        self.play(
            ring_a.animate.scale(9).set_stroke(opacity=0),
            ring_b.animate.scale(12).set_stroke(opacity=0),
            ApplyWave(chars, amplitude=0.12, time_width=0.6),
            run_time=0.55,
            rate_func=smooth,
        )
        self.remove(ring_a, ring_b)

        # 合并为单 Text，Transform 到左上（OpeningManim 同款）
        title = Text("内容总览", font=UI_FONT, font_size=56, color=C_TITLE)
        title.set_color_by_gradient(FAV[0], FAV[1], RAINBOW[5])
        title.move_to(chars)
        self.remove(chars)
        self.add(title)

        target_ul = Text("内容总览", font=UI_FONT, font_size=36, color=C_TITLE)
        target_ul.set_color_by_gradient(FAV[0], FAV[1])
        target_ul.to_corner(UL, buff=0.48)
        accent = Line(ORIGIN, RIGHT * 2.0, stroke_color=FAV[0], stroke_width=2.5)
        accent.next_to(target_ul, DOWN, buff=0.18).align_to(target_ul, LEFT)

        self.play(
            Transform(title, target_ul),
            Transform(underline, accent),
            run_time=0.8,
            rate_func=smooth,
        )
        head = title
        accent_line = underline
        self.wait(0.1)

        # ── 四行目录 ─────────────────────────────────────────────────────
        rows = VGroup(
            *[_chapter_row(n, t, b, RAINBOW[i % 7]) for i, (n, t, b) in enumerate(MODULES)]
        )
        rows.arrange(DOWN, buff=0.52, aligned_edge=LEFT)
        rows.next_to(accent_line, DOWN, buff=0.42).align_to(head, LEFT)
        if rows.get_right()[0] > 6.3:
            rows.set_width(11.8)
            rows.next_to(accent_line, DOWN, buff=0.42).align_to(head, LEFT)
        if rows.get_bottom()[1] < -3.15:
            rows.scale(0.92)
            rows.next_to(accent_line, DOWN, buff=0.38).align_to(head, LEFT)

        lines = VGroup()
        for i in range(len(rows) - 1):
            a = rows[i][0].get_center()
            b = rows[i + 1][0].get_center()
            ln = Line(a, b, stroke_width=3)
            ln.set_color_by_gradient(RAINBOW[i % 7], RAINBOW[(i + 1) % 7])
            lines.add(ln)

        self.play(
            LaggedStart(*[FadeIn(r, shift=RIGHT * 0.22) for r in rows], lag_ratio=0.12),
            run_time=0.7,
            rate_func=smooth,
        )

        # 每章约 3s
        prev_glow = None
        for i, row in enumerate(rows):
            accent_c = RAINBOW[i % 7]
            glow = SurroundingRectangle(
                row,
                buff=0.14,
                corner_radius=0.1,
                color=accent_c,
                stroke_width=1.6,
            )
            glow.set_stroke(opacity=0.85)

            if i == 0:
                self.play(
                    Create(glow),
                    row[1].animate.set_color(accent_c),
                    row[2][0].animate.set_color(WHITE),
                    run_time=0.5,
                    rate_func=smooth,
                )
                prev_glow = glow
            else:
                self.play(
                    Transform(prev_glow, glow),
                    rows[i - 1][2][0].animate.set_color(C_TITLE),
                    row[2][0].animate.set_color(WHITE),
                    Create(lines[i - 1]),
                    run_time=0.55,
                    rate_func=smooth,
                )

            center = row[0].get_center()
            rings, sparks = _shockwave_burst(center, accent_c)
            self.add(rings, sparks)
            self.play(
                LaggedStart(
                    *[rings[k].animate.scale(3.2 + k).set_stroke(opacity=0) for k in range(3)],
                    *[s.animate.shift(s.shift_vec).set_opacity(0) for s in sparks],  # type: ignore[attr-defined]
                    lag_ratio=0.04,
                ),
                run_time=0.35,
                rate_func=smooth,
            )
            self.remove(rings, sparks)
            self.wait(1.55)

        self.wait(0.55)

# ── 冲击波标题 ──────────────────────────────────────────────

C_BG = "#07090f"
C_SUB = "#a8b4c8"
C_MUTED = "#7a879c"
C_HOT = "#ff6b4a"
C_WARM = "#feac5e"
C_COOL = "#4bc0c8"
C_PANEL = "#0c121c"
C_WALL = "#6a7588"
C_SAFE = "#4ade80"
C_TITLE = "#f1f5ff"

EASE = rate_functions.ease_in_out_cubic


def _safe_ui_font() -> str:
    try:
        from manim.utils.fonts import get_available_fonts

        available = set(get_available_fonts())
        for name in (*text_font, "Microsoft YaHei", "SimHei", "Noto Sans CJK SC", "Sans"):
            if name in available:
                return name
    except Exception:
        pass
    return "Sans"


UI_FONT = _safe_ui_font()


def _soft_grid() -> VGroup:
    g = VGroup()
    for x in np.arange(-7.2, 7.3, 0.75):
        op = 0.18 if abs(x) < 0.01 else 0.1
        g.add(
            Line([x, -4, 0], [x, 4, 0], stroke_color="#d8e0ec", stroke_width=1.0, stroke_opacity=op)
        )
    for y in np.arange(-4.0, 4.1, 0.75):
        op = 0.18 if abs(y) < 0.01 else 0.1
        g.add(
            Line([-7.2, y, 0], [7.2, y, 0], stroke_color="#d8e0ec", stroke_width=1.0, stroke_opacity=op)
        )
    return g


def _bullets(lines: list[str], color: str = C_TITLE, size: int = 17) -> VGroup:
    items = VGroup()
    for s in lines:
        dot = Dot(radius=0.045, color=color)
        txt = Text(s, font=UI_FONT, font_size=size, color=C_TITLE)
        items.add(VGroup(dot, txt).arrange(RIGHT, buff=0.16, aligned_edge=DOWN))
    return items.arrange(DOWN, buff=0.16, aligned_edge=LEFT)


def _check_mark(color: str = C_SAFE) -> VGroup:
    """Geometric check — avoid Text('✓') tofu / white glyph box."""
    p1 = np.array([-0.1, 0.02, 0.0])
    p2 = np.array([-0.02, -0.08, 0.0])
    p3 = np.array([0.16, 0.12, 0.0])
    return VGroup(
        Line(p1, p2, stroke_color=color, stroke_width=3.0),
        Line(p2, p3, stroke_color=color, stroke_width=3.0),
    )


def _demo_frame(accent: str, width: float = 5.0, height: float = 2.35) -> tuple[RoundedRectangle, RoundedRectangle]:
    """Fill + border split so border stays on top of the wave circle."""
    fill = RoundedRectangle(
        width=width,
        height=height,
        corner_radius=0.12,
        fill_color=C_PANEL,
        fill_opacity=0.95,
        stroke_width=0,
    )
    border = RoundedRectangle(
        width=width,
        height=height,
        corner_radius=0.12,
        fill_opacity=0,
        stroke_color=accent,
        stroke_width=2.0,
        stroke_opacity=0.9,
    )
    return fill, border


def _mini_scene() -> tuple[VGroup, Dot, Dot, Line]:
    """Tight schematic so blast circle stays inside the demo frame."""
    # 水平跨度压短，保证圆半径 < 框半高
    bomb = Dot(LEFT * 0.58, radius=0.075, color=C_WARM)
    bomb.set_stroke(WHITE, width=1.0, opacity=0.65)
    player = Dot(RIGHT * 0.42 + UP * 0.06, radius=0.075, color=C_COOL)
    player.set_stroke(WHITE, width=1.0, opacity=0.65)
    wall = Line(UP * 0.48, DOWN * 0.48, stroke_color=C_WALL, stroke_width=5.5)
    wall.move_to(RIGHT * 0.02)
    lb = Text("C4", font="Consolas", font_size=11, color=C_MUTED).next_to(bomb, DOWN, buff=0.08)
    lp = Text("P", font="Consolas", font_size=11, color=C_MUTED).next_to(player, DOWN, buff=0.08)
    props = VGroup(wall, bomb, player, lb, lp)
    return props, bomb, player, wall


def _max_radius_in_frame(center: np.ndarray, frame: Mobject, pad: float = 0.14) -> float:
    """Largest circle radius from center that stays inside frame."""
    left = frame.get_left()[0] + pad
    right = frame.get_right()[0] - pad
    bottom = frame.get_bottom()[1] + pad
    top = frame.get_top()[1] - pad
    return float(
        min(
            center[0] - left,
            right - center[0],
            center[1] - bottom,
            top - center[1],
        )
    )


class ShockwaveTitleScene(Scene):
    """冲击波算法：标题 → 对照介绍（文字主、示意为辅）。"""

    def construct(self):
        self.camera.background_color = ManimColor(C_BG)
        self.add(_soft_grid())

        # ── 1) 开场（略收，给后面介绍留时间）──────────────────────────
        core = Dot(ORIGIN, radius=0.055, color=C_HOT)
        blast = Circle(radius=3.4, color=C_WARM, stroke_width=2.0)
        self.play(
            Flash(core, color=C_WARM, line_length=0.3, num_lines=10, flash_radius=0.5),
            run_time=0.3,
        )
        self.play(
            Broadcast(
                blast,
                focal_point=ORIGIN,
                n_mobs=3,
                initial_opacity=0.8,
                final_opacity=0,
                lag_ratio=0.2,
                remover=True,
            ),
            FadeOut(core),
            run_time=0.85,
            rate_func=EASE,
        )

        badge = Text("01", font="Consolas", font_size=18, color=C_HOT)
        title = Text("冲击波算法", font=UI_FONT, font_size=52, color=C_TITLE)
        title.set_color_by_gradient(C_HOT, C_WARM, C_COOL)
        underline = Line(LEFT, RIGHT, stroke_color=C_WARM, stroke_width=2.6)
        underline.set_width(title.width * 0.9)
        en = Text("SHOCKWAVE ALGORITHM", font="Consolas", font_size=15, color=C_MUTED)
        stack = VGroup(badge, title, underline, en).arrange(DOWN, buff=0.24).move_to(ORIGIN)

        self.play(
            FadeIn(badge, shift=DOWN * 0.12),
            FadeIn(title, shift=UP * 0.15),
            Create(underline),
            FadeIn(en),
            run_time=0.95,
            rate_func=EASE,
        )
        self.wait(0.55)

        # ── 2) Transform 收束 ─────────────────────────────────────────
        title_ul = Text("冲击波算法", font=UI_FONT, font_size=28, color=C_TITLE)
        title_ul.set_color_by_gradient(C_HOT, C_WARM)
        title_ul.to_corner(UL, buff=0.42)
        line_ul = Line(ORIGIN, RIGHT * 1.85, stroke_color=C_WARM, stroke_width=2.2)
        line_ul.next_to(title_ul, DOWN, buff=0.12).align_to(title_ul, LEFT)

        self.play(
            FadeOut(badge),
            FadeOut(en),
            Transform(title, title_ul),
            Transform(underline, line_ul),
            run_time=0.85,
            rate_func=EASE,
        )

        # ── 3) 导语（主信息，先读懂再看图）────────────────────────────
        lead = Text(
            "同一场景：墙后有人。两种模型，结论完全不同。",
            font=UI_FONT,
            font_size=22,
            color=C_TITLE,
        )
        lead_sub = Text(
            "左边按直线距离；右边按冲击波能否绕到你。",
            font=UI_FONT,
            font_size=16,
            color=C_SUB,
        )
        lead_block = VGroup(lead, lead_sub).arrange(DOWN, buff=0.14, aligned_edge=LEFT)
        lead_block.next_to(VGroup(title, underline), DOWN, buff=0.38).align_to(title, LEFT)
        if lead_block.get_right()[0] > 6.4:
            lead.set_width(11.5)
            lead_sub.set_width(11.5)
            lead_block.arrange(DOWN, buff=0.14, aligned_edge=LEFT)
            lead_block.next_to(VGroup(title, underline), DOWN, buff=0.38).align_to(title, LEFT)

        self.play(FadeIn(lead, shift=UP * 0.08), run_time=0.55, rate_func=EASE)
        self.wait(0.45)
        self.play(FadeIn(lead_sub, shift=UP * 0.06), run_time=0.45, rate_func=EASE)
        self.wait(0.55)

        # ── 4) 双栏文字介绍（主）+ 小示意（辅）────────────────────────
        # 左栏
        l_title = Text("旧 · 欧氏球体", font=UI_FONT, font_size=26, color=C_HOT)
        l_points = _bullets(
            ["用直线距离判断是否受伤", "半径球会穿过墙壁", "墙后很近 → 仍可能满伤"],
            color=C_HOT,
            size=16,
        )
        l_fill, l_border = _demo_frame(C_HOT)
        l_props, l_bomb, l_player, _ = _mini_scene()
        l_props.move_to(l_fill.get_center())
        l_demo = VGroup(l_fill, l_props, l_border)
        l_tag = Text("示意：穿墙命中", font=UI_FONT, font_size=14, color=C_MUTED)
        left = VGroup(l_title, l_points, l_demo, l_tag).arrange(DOWN, buff=0.22, aligned_edge=LEFT)

        # 右栏
        r_title = Text("新 · 路径波前", font=UI_FONT, font_size=26, color=C_COOL)
        r_points = _bullets(
            ["用绕墙最短路径判断", "冲击波不能穿墙，只能绕", "墙后近 ≠ 危险，绕不开才安全"],
            color=C_COOL,
            size=16,
        )
        r_fill, r_border = _demo_frame(C_COOL)
        r_props, r_bomb, r_player, r_wall = _mini_scene()
        r_props.move_to(r_fill.get_center())
        r_demo = VGroup(r_fill, r_props, r_border)
        r_tag = Text("示意：绕墙到达", font=UI_FONT, font_size=14, color=C_MUTED)
        right = VGroup(r_title, r_points, r_demo, r_tag).arrange(DOWN, buff=0.22, aligned_edge=LEFT)

        vs = Text("VS", font="Consolas", font_size=18, color=C_MUTED)
        divider = Line(UP * 2.1, DOWN * 2.1, stroke_color="#2e3a4e", stroke_width=1.1)
        cols = VGroup(left, divider, right).arrange(RIGHT, buff=0.45, aligned_edge=UP)
        vs.move_to(divider.get_center())
        compare = VGroup(cols, vs)
        compare.next_to(lead_block, DOWN, buff=0.4)
        compare.set_x(0)
        # 垂直居中剩余空间，避免底下空一大块
        top_y = lead_block.get_bottom()[1] - 0.35
        bot_y = -3.35
        mid = (top_y + bot_y) / 2
        compare.move_to([0, mid, 0])

        # 刷新示意坐标；圆半径限制在框内
        l_bc, l_pc = l_bomb.get_center(), l_player.get_center()
        r_bc, r_pc = r_bomb.get_center(), r_player.get_center()
        hit_r = min(
            float(np.linalg.norm(l_pc - l_bc)) + 0.04,
            _max_radius_in_frame(l_bc, l_fill, pad=0.16),
        )

        # 先出文字标题与要点（主）；示意稍后出场
        self.play(
            FadeIn(l_title, shift=RIGHT * 0.12),
            FadeIn(r_title, shift=LEFT * 0.12),
            FadeIn(vs, scale=0.85),
            Create(divider),
            run_time=0.7,
            rate_func=EASE,
        )
        self.play(
            LaggedStart(*[FadeIn(m, shift=UP * 0.06) for m in l_points], lag_ratio=0.15),
            LaggedStart(*[FadeIn(m, shift=UP * 0.06) for m in r_points], lag_ratio=0.15),
            run_time=1.15,
            rate_func=EASE,
        )
        self.wait(0.85)  # 留时间读文字

        # 再出小示意（辅）：底填 → 内容 → 边框置顶
        self.play(
            FadeIn(l_fill),
            FadeIn(r_fill),
            FadeIn(l_props),
            FadeIn(r_props),
            FadeIn(l_border),
            FadeIn(r_border),
            run_time=0.65,
            rate_func=EASE,
        )
        self.bring_to_front(l_border, r_border)

        # 左示意：圆不超出框
        l_r = ValueTracker(0.04)
        l_circle = always_redraw(
            lambda: Circle(
                radius=max(min(l_r.get_value(), hit_r), 0.02),
                stroke_color=C_HOT,
                stroke_width=2.0,
                stroke_opacity=0.85,
            )
            .move_to(l_bc)
            .set_fill(C_HOT, opacity=0.1)
        )
        self.add(l_circle)
        self.bring_to_front(l_props, l_border)
        self.play(l_r.animate.set_value(hit_r), run_time=0.95, rate_func=EASE)
        cross = VGroup(Line(UL * 0.1, DR * 0.1), Line(UR * 0.1, DL * 0.1)).set_stroke(C_HOT, 2.6)
        cross.move_to(l_pc)
        self.play(FadeIn(cross, scale=0.7), FadeIn(l_tag), run_time=0.4, rate_func=EASE)
        self.bring_to_front(l_border)
        self.wait(0.35)

        # 右示意：路径压在框内
        blocked = DashedLine(r_bc, r_pc, stroke_color=C_HOT, stroke_width=1.4, dash_length=0.1)
        blocked.set_opacity(0.4)
        # 下绕幅度受框底约束
        y_floor = r_fill.get_bottom()[1] + 0.22
        mid_y = max(r_bc[1] - 0.55, y_floor)
        detour = [
            r_bc,
            np.array([r_bc[0] + 0.05, mid_y, 0.0]),
            np.array([r_pc[0], mid_y, 0.0]),
            r_pc,
        ]
        path = VMobject().set_points_as_corners(detour).set_stroke(C_COOL, width=2.6, opacity=0.9)
        tip = Dot(detour[0], radius=0.05, color=C_COOL)

        self.play(Create(blocked), run_time=0.35, rate_func=EASE)
        self.play(FadeOut(blocked), Create(path), MoveAlongPath(tip, path), run_time=1.05, rate_func=EASE)
        check = _check_mark(C_SAFE).move_to(r_pc + UP * 0.22)
        self.play(FadeIn(check, scale=0.75), FadeIn(r_tag), run_time=0.4, rate_func=EASE)
        self.bring_to_front(r_border)

        self.wait(1.6)

# ── 搜索算法标题 ────────────────────────────────────────────

C_BG = "#07090f"
C_SUB = "#a8b4c8"
C_MUTED = "#7a879c"
C_HOT = "#ff6b4a"
C_WARM = "#feac5e"
C_COOL = "#4bc0c8"
C_PURPLE = "#a78bfa"
C_PANEL = "#0c121c"
C_WALL = "#6a7588"
C_TITLE = "#f1f5ff"
C_START = "#ff6b4a"
C_GOAL = "#5eead4"
# 软网格：偏冷灰、低透明度（与冲击波 title 一致，避免发白）
C_GRID = "#5a6578"

EASE = rate_functions.ease_in_out_cubic


def _safe_ui_font() -> str:
    try:
        from manim.utils.fonts import get_available_fonts

        available = set(get_available_fonts())
        for name in (*text_font, "Microsoft YaHei", "SimHei", "Noto Sans CJK SC", "Sans"):
            if name in available:
                return name
    except Exception:
        pass
    return "Sans"


UI_FONT = _safe_ui_font()


def _soft_grid() -> VGroup:
    """与冲击波 title 同款软网格：低对比，不抢前景。"""
    g = VGroup()
    for x in np.arange(-7.2, 7.3, 0.75):
        op = 0.14 if abs(x) < 0.01 else 0.07
        g.add(
            Line([x, -4, 0], [x, 4, 0], stroke_color=C_GRID, stroke_width=0.9, stroke_opacity=op)
        )
    for y in np.arange(-4.0, 4.1, 0.75):
        op = 0.14 if abs(y) < 0.01 else 0.07
        g.add(
            Line([-7.2, y, 0], [7.2, y, 0], stroke_color=C_GRID, stroke_width=0.9, stroke_opacity=op)
        )
    return g


def _stroke_only(mob: Mobject) -> Mobject:
    """强制纯描边，避免 Create/默认样式带出填充。"""
    mob.set_fill(color=BLACK, opacity=0)
    return mob


def _algo_card(name: str, lines: list[str], accent: str, glyph: Mobject, *, key: str = "") -> VGroup:
    """卡片：不用占位 Rectangle（set_opacity 会把它变成白底）。"""
    fill = RoundedRectangle(
        width=2.28,
        height=3.05,
        corner_radius=0.12,
        fill_color=C_PANEL,
        fill_opacity=0.95,
        stroke_color=accent,
        stroke_width=1.8,
        stroke_opacity=0.9,
    )
    # 图标缩放到固定视觉高度，用手动布局对齐分隔线
    icon_top = fill.get_top()[1] - 0.32
    icon_h = 1.15
    if glyph.width > 1.7:
        glyph.scale_to_fit_width(1.7)
    if glyph.height > icon_h * 0.92:
        glyph.scale_to_fit_height(icon_h * 0.92)
    glyph.move_to([fill.get_center()[0], icon_top - icon_h / 2, 0])

    bar = Line(LEFT * 0.85, RIGHT * 0.85, stroke_color=accent, stroke_width=2.4)
    bar.move_to([fill.get_center()[0], icon_top - icon_h - 0.14, 0])

    title = Text(name, font=UI_FONT, font_size=20, color=accent)
    title.next_to(bar, DOWN, buff=0.16)
    title.set_x(fill.get_center()[0])

    body = VGroup(*[Text(s, font=UI_FONT, font_size=13, color=C_SUB) for s in lines])
    body.arrange(DOWN, buff=0.08, aligned_edge=LEFT)
    body.next_to(title, DOWN, buff=0.14)
    body.set_x(fill.get_center()[0])

    # 图层：底框 → 文字 → 图标置顶（动画细节不被挡住）
    card = VGroup(fill, bar, title, body, glyph)
    card.accent = accent  # type: ignore[attr-defined]
    card.glyph = glyph  # type: ignore[attr-defined]
    card.fill = fill  # type: ignore[attr-defined]
    card.bar = bar  # type: ignore[attr-defined]
    card.title_m = title  # type: ignore[attr-defined]
    card.body_m = body  # type: ignore[attr-defined]
    card.glyph_key = key  # type: ignore[attr-defined]
    return card


def _hide_glyph_parts(glyph: Mobject) -> list[Mobject]:
    def _leaves(mob: Mobject) -> list[Mobject]:
        if isinstance(mob, VGroup) and len(mob) > 0 and not isinstance(mob, Text):
            out: list[Mobject] = []
            for sub in mob:
                out.extend(_leaves(sub))
            return out or [mob]
        return [mob]

    glyph.set_z_index(5)
    parts = _leaves(glyph)
    for p in parts:
        if not isinstance(p, (Dot, Text, Triangle)):
            _stroke_only(p)
        p.set_z_index(6)
        p.set_opacity(0)
    return parts


def _show_stroke(p: Mobject) -> None:
    if not isinstance(p, (Dot, Text, Triangle)):
        _stroke_only(p)
    p.set_opacity(1)
    p.set_z_index(6)


def _play_glyph_build(scene: Scene, glyph: Mobject, *, key: str = "", run_time: float = 0.7) -> None:
    """按算法语义编排图示；图标始终置顶，避免被卡面挡住。"""
    scene.bring_to_front(glyph)
    parts = _hide_glyph_parts(glyph)
    ease = EASE

    if key == "euclid" and len(glyph) >= 5:
        wall, ring, cross, s, g = glyph[0], glyph[1], glyph[2], glyph[3], glyph[4]
        _show_stroke(wall)
        scene.play(FadeIn(wall), run_time=0.12)
        _show_stroke(ring)
        scene.play(GrowFromCenter(ring), run_time=0.28, rate_func=ease)
        _stroke_only(ring)
        scene.play(FadeIn(s, scale=0.8), FadeIn(g, scale=0.8), run_time=0.18)
        _show_stroke(cross)
        scene.play(FadeIn(cross), run_time=0.18)
    elif key == "bfs" and len(glyph) >= 2:
        rings, s = glyph[0], glyph[1]
        scene.play(FadeIn(s, scale=0.8), run_time=0.15)
        for sq in rings:
            _show_stroke(sq)
        scene.play(
            LaggedStart(*[GrowFromCenter(sq) for sq in rings], lag_ratio=0.28),
            run_time=0.55,
            rate_func=ease,
        )
        for sq in rings:
            _stroke_only(sq)
            sq.set_opacity(1)
    elif key == "dijkstra" and len(glyph) >= 5:
        dots, seg1, seg2, s, g = glyph[0], glyph[1], glyph[2], glyph[3], glyph[4]
        scene.play(FadeIn(s, scale=0.8), run_time=0.12)
        _show_stroke(seg1)
        scene.play(FadeIn(seg1), FadeIn(dots[0], scale=0.85), run_time=0.22)
        _show_stroke(seg2)
        scene.play(FadeIn(seg2), FadeIn(g, scale=0.8), run_time=0.22)
        scene.play(FadeIn(dots[1], scale=0.85), FadeIn(dots[2], scale=0.85), run_time=0.18)
    elif key == "astar" and len(glyph) >= 4:
        wedge, path, s, g = glyph[0], glyph[1], glyph[2], glyph[3]
        scene.play(FadeIn(s, scale=0.8), run_time=0.12)
        _show_stroke(path)
        scene.play(FadeIn(path), run_time=0.22)
        _show_stroke(wedge)
        scene.play(FadeIn(wedge), FadeIn(g, scale=0.8), run_time=0.28)
        _stroke_only(wedge)
        wedge.set_opacity(1)
    elif key == "greedy" and len(glyph) >= 5:
        shaft, tip, h, s, g = glyph[0], glyph[1], glyph[2], glyph[3], glyph[4]
        scene.play(FadeIn(s, scale=0.8), run_time=0.12)
        _show_stroke(shaft)
        scene.play(FadeIn(shaft), run_time=0.2)
        tip.set_opacity(1)
        tip.set_z_index(7)
        scene.play(FadeIn(tip, scale=0.7), FadeIn(g, scale=0.8), run_time=0.2)
        h.set_opacity(1)
        scene.play(FadeIn(h, shift=UP * 0.05), run_time=0.15)
    else:
        anims = []
        for p in parts:
            if not isinstance(p, (Dot, Text, Triangle)):
                _stroke_only(p)
            p.set_opacity(0)
            anims.append(FadeIn(p, scale=0.92))
        scene.play(LaggedStart(*anims, lag_ratio=0.18), run_time=run_time, rate_func=ease)

    for p in parts:
        if not isinstance(p, (Dot, Text, Triangle)):
            _stroke_only(p)
        p.set_opacity(1)
        p.set_z_index(6)
    scene.bring_to_front(glyph)


def _glyph_euclid() -> VGroup:
    s = Dot(LEFT * 0.32, radius=0.055, color=C_START)
    g = Dot(RIGHT * 0.32, radius=0.055, color=C_GOAL)
    wall = Line(UP * 0.28, DOWN * 0.28, stroke_color=C_WALL, stroke_width=3.5)
    ring = _stroke_only(Circle(radius=0.55, stroke_color=C_HOT, stroke_width=1.6, stroke_opacity=0.85))
    cross = DashedLine(s.get_center(), g.get_center(), stroke_color=C_HOT, stroke_width=1.2, dash_length=0.08)
    cross.set_opacity(0.55)
    return VGroup(wall, ring, cross, s, g)


def _glyph_bfs() -> VGroup:
    s = Dot(ORIGIN, radius=0.05, color=C_START)
    rings = VGroup()
    for k in range(3):
        sq = Square(
            side_length=0.35 + 0.28 * k,
            stroke_color=C_COOL,
            stroke_width=1.5,
            stroke_opacity=0.35 + 0.2 * k,
        )
        _stroke_only(sq)
        rings.add(sq)
    return VGroup(rings, s)


def _glyph_dijkstra() -> VGroup:
    """折线用两段 Line，避免 VMobject 折角被当成填充三角。"""
    s = Dot(LEFT * 0.35 + DOWN * 0.15, radius=0.05, color=C_START)
    g = Dot(RIGHT * 0.35 + UP * 0.15, radius=0.05, color=C_GOAL)
    mid = LEFT * 0.05 + UP * 0.32
    seg1 = _stroke_only(Line(s.get_center(), mid, stroke_color=C_WARM, stroke_width=2.2))
    seg2 = _stroke_only(Line(mid, g.get_center(), stroke_color=C_WARM, stroke_width=2.2))
    dots = VGroup(
        Dot(mid, radius=0.035, color=C_WARM),
        Dot(LEFT * 0.18 + DOWN * 0.05, radius=0.03, color=C_WARM).set_opacity(0.5),
        Dot(RIGHT * 0.12 + DOWN * 0.2, radius=0.03, color=C_WARM).set_opacity(0.35),
    )
    return VGroup(dots, seg1, seg2, s, g)


def _glyph_astar() -> VGroup:
    s = Dot(LEFT * 0.38 + DOWN * 0.2, radius=0.05, color=C_START)
    g = Dot(RIGHT * 0.35 + UP * 0.22, radius=0.05, color=C_GOAL)
    wedge = Arc(
        radius=0.62,
        start_angle=-0.35,
        angle=1.05,
        arc_center=s.get_center(),
        stroke_color=C_PURPLE,
        stroke_width=2.0,
        stroke_opacity=0.75,
    )
    _stroke_only(wedge)
    path = _stroke_only(Line(s.get_center(), g.get_center(), stroke_color=C_PURPLE, stroke_width=2.0))
    path.set_stroke(opacity=0.9)
    return VGroup(wedge, path, s, g)


def _glyph_greedy() -> VGroup:
    s = Dot(LEFT * 0.38, radius=0.05, color=C_START)
    g = Dot(RIGHT * 0.38, radius=0.05, color=C_GOAL)
    # 箭头尖需要一点填充；杆用 Line 避免整段被填实
    shaft = _stroke_only(
        Line(
            s.get_center() + RIGHT * 0.1,
            g.get_center() + LEFT * 0.16,
            stroke_color="#fb923c",
            stroke_width=2.2,
        )
    )
    tip = Triangle(fill_color="#fb923c", fill_opacity=1, stroke_width=0)
    tip.scale(0.08)
    tip.rotate(-PI / 2)
    tip.move_to(g.get_center() + LEFT * 0.12)
    h = Text("h", font="Consolas", font_size=14, color="#fb923c").next_to(shaft, UP, buff=0.06)
    return VGroup(shaft, tip, h, s, g)


@dataclass
class TitleCardResult:
    """标题卡结束后仍保留 / 待淡出的物件。"""

    title: Mobject
    underline: Mobject
    fade_group: VGroup
    grid: VGroup


def play_pathfinding_title_card(scene: Scene, *, hold_tail: float = 0.85) -> TitleCardResult:
    """播放开场标题 + 五算法总览。返回可衔接到讲解段的 chrome。"""
    grid = _soft_grid()
    scene.add(grid)

    core = Dot(ORIGIN, radius=0.05, color=C_COOL)
    ring = Circle(radius=3.2, color=C_PURPLE, stroke_width=1.8)
    scene.play(
        Flash(core, color=C_COOL, line_length=0.28, num_lines=10, flash_radius=0.45),
        run_time=0.3,
    )
    scene.play(
        Broadcast(
            ring,
            focal_point=ORIGIN,
            n_mobs=3,
            initial_opacity=0.75,
            final_opacity=0,
            lag_ratio=0.22,
            remover=True,
        ),
        FadeOut(core),
        run_time=0.85,
        rate_func=EASE,
    )

    badge = Text("02", font="Consolas", font_size=18, color=C_COOL)
    title = Text("搜索算法拓展", font=UI_FONT, font_size=50, color=C_TITLE)
    title.set_color_by_gradient(C_COOL, C_PURPLE, C_WARM)
    underline = Line(LEFT, RIGHT, stroke_color=C_COOL, stroke_width=2.6)
    underline.set_width(title.width * 0.9)
    en = Text("PATHFINDING · DISTANCE FIELDS", font="Consolas", font_size=14, color=C_MUTED)
    VGroup(badge, title, underline, en).arrange(DOWN, buff=0.24).move_to(ORIGIN)

    scene.play(
        FadeIn(badge, shift=DOWN * 0.12),
        FadeIn(title, shift=UP * 0.15),
        Create(underline),
        FadeIn(en),
        run_time=0.95,
        rate_func=EASE,
    )
    scene.wait(0.45)

    title_ul = Text("搜索算法拓展", font=UI_FONT, font_size=26, color=C_TITLE)
    title_ul.set_color_by_gradient(C_COOL, C_PURPLE)
    title_ul.to_corner(UL, buff=0.42)
    line_ul = Line(ORIGIN, RIGHT * 2.15, stroke_color=C_COOL, stroke_width=2.2)
    line_ul.next_to(title_ul, DOWN, buff=0.12).align_to(title_ul, LEFT)

    scene.play(
        FadeOut(badge),
        FadeOut(en),
        Transform(title, title_ul),
        Transform(underline, line_ul),
        run_time=0.85,
        rate_func=EASE,
    )

    lead = Text(
        "同一张地图，五种距离 / 搜索模型，各管一件事。",
        font=UI_FONT,
        font_size=22,
        color=C_TITLE,
    )
    lead_sub = Text(
        "欧氏 · BFS · Dijkstra · A* · 贪心 — 先建立总览，后面逐个展开。",
        font=UI_FONT,
        font_size=16,
        color=C_SUB,
    )
    lead_block = VGroup(lead, lead_sub).arrange(DOWN, buff=0.14, aligned_edge=LEFT)
    lead_block.next_to(VGroup(title, underline), DOWN, buff=0.36).align_to(title, LEFT)
    if lead_block.get_right()[0] > 6.4:
        lead.set_width(11.5)
        lead_sub.set_width(11.5)
        lead_block.arrange(DOWN, buff=0.14, aligned_edge=LEFT)
        lead_block.next_to(VGroup(title, underline), DOWN, buff=0.36).align_to(title, LEFT)

    scene.play(FadeIn(lead, shift=UP * 0.08), run_time=0.5, rate_func=EASE)
    scene.wait(0.25)
    scene.play(FadeIn(lead_sub, shift=UP * 0.06), run_time=0.4, rate_func=EASE)
    scene.wait(0.3)

    section = Text("五种模型 · 总览", font=UI_FONT, font_size=18, color=C_MUTED)
    section.next_to(lead_block, DOWN, buff=0.28).align_to(lead_block, LEFT)

    cards = VGroup(
        _algo_card("欧氏", ["直线距离", "无视墙体"], C_HOT, _glyph_euclid(), key="euclid"),
        _algo_card("BFS", ["单位步长", "一层层外扩"], C_COOL, _glyph_bfs(), key="bfs"),
        _algo_card("Dijkstra", ["带权最短路", "精确累计代价"], C_WARM, _glyph_dijkstra(), key="dijkstra"),
        _algo_card("A*", ["g + h 引导", "少探索仍最优"], C_PURPLE, _glyph_astar(), key="astar"),
        _algo_card("贪心", ["只看 h", "快但不保证优"], "#fb923c", _glyph_greedy(), key="greedy"),
    ).arrange(RIGHT, buff=0.22)

    # 二次对齐：五张卡分隔线同一水平线
    bar_y = cards[0].bar.get_center()[1]
    for card in cards:
        dy = bar_y - card.bar.get_center()[1]
        card.bar.shift(UP * dy)
        card.title_m.shift(UP * dy)
        card.body_m.shift(UP * dy)

    top_y = section.get_bottom()[1] - 0.22
    bot_y = -3.45
    cards.move_to([0, (top_y + bot_y) / 2, 0])

    bar_y = cards[0].bar.get_center()[1]
    for card in cards:
        dy = bar_y - card.bar.get_center()[1]
        card.bar.shift(UP * dy)
        card.title_m.shift(UP * dy)
        card.body_m.shift(UP * dy)

    arrows = VGroup()
    for i in range(len(cards) - 1):
        a = Arrow(
            cards[i].get_right() + RIGHT * 0.02,
            cards[i + 1].get_left() + LEFT * 0.02,
            buff=0.02,
            stroke_width=1.4,
            color="#2e3a4e",
            max_tip_length_to_length_ratio=0.35,
            tip_length=0.1,
        )
        a.set_opacity(0.7)
        arrows.add(a)

    scene.play(FadeIn(section, shift=UP * 0.06), run_time=0.3, rate_func=EASE)

    # 逐张完整点亮；绝不对整卡 set_opacity（会把透明槽/描边变成白底）
    for card in cards:
        card.bar.set_opacity(0)
        card.title_m.set_opacity(0)
        card.body_m.set_opacity(0)
        for p in card.glyph.family_members_with_points():
            if not isinstance(p, (Dot, Text, Triangle)):
                _stroke_only(p)
            p.set_opacity(0)
        card.fill.set_opacity(0)

    for card in cards:
        card.fill.set_opacity(1)
        scene.play(FadeIn(card.fill, scale=0.97), run_time=0.28, rate_func=EASE)
        scene.bring_to_front(card.glyph)
        _play_glyph_build(scene, card.glyph, key=getattr(card, "glyph_key", ""), run_time=0.55)
        card.bar.set_opacity(1)
        card.title_m.set_opacity(1)
        card.body_m.set_opacity(1)
        scene.play(
            FadeIn(card.bar),
            Write(card.title_m),
            LaggedStart(*[Write(line) for line in card.body_m], lag_ratio=0.12),
            run_time=0.5,
            rate_func=EASE,
        )
        scene.bring_to_front(card.glyph)
        scene.play(card.fill.animate.set_stroke(width=3.2), run_time=0.18, rate_func=EASE)
        scene.play(card.fill.animate.set_stroke(width=1.8), run_time=0.14, rate_func=EASE)

    # 收尾：描边复位，图标置顶，禁止整卡 set_opacity
    for card in cards:
        card.fill.set_fill(C_PANEL, opacity=0.95)
        card.fill.set_stroke(color=card.accent, width=1.8, opacity=0.9)
        for p in card.glyph.family_members_with_points():
            if not isinstance(p, (Dot, Text, Triangle)):
                _stroke_only(p)
            p.set_opacity(1)
        scene.bring_to_front(card.glyph)

    scene.play(
        LaggedStart(*[FadeIn(a, scale=0.85) for a in arrows], lag_ratio=0.1),
        run_time=0.35,
    )
    scene.wait(hold_tail)

    fade_group = VGroup(lead, lead_sub, section, cards, arrows)
    return TitleCardResult(title=title, underline=underline, fade_group=fade_group, grid=grid)


class PathfindingTitleScene(Scene):
    """搜索算法拓展 · 标题卡（文主图辅，风格对齐冲击波 title）。"""

    def construct(self):
        self.camera.background_color = ManimColor(C_BG)
        play_pathfinding_title_card(self, hold_tail=1.4)

# ── 预烘焙标题 ──────────────────────────────────────────────

C_BG = "#07090f"
C_SUB = "#a8b4c8"
C_MUTED = "#7a879c"
C_HOT = "#ff6b4a"
C_WARM = "#feac5e"
C_COOL = "#4bc0c8"
C_PURPLE = "#a78bfa"
C_BAKE = "#f0a040"
C_SAVE = "#5eead4"
C_PANEL = "#0c121c"
C_TITLE = "#f1f5ff"
C_GRID = "#5a6578"

EASE = rate_functions.ease_in_out_cubic


def _safe_ui_font() -> str:
    try:
        from manim.utils.fonts import get_available_fonts

        available = set(get_available_fonts())
        for name in (*text_font, "Microsoft YaHei", "SimHei", "Noto Sans CJK SC", "Sans"):
            if name in available:
                return name
    except Exception:
        pass
    return "Sans"


UI_FONT = _safe_ui_font()


def _soft_grid() -> VGroup:
    """与 01/02 title 同款软网格：低对比，不抢前景。"""
    g = VGroup()
    for x in np.arange(-7.2, 7.3, 0.75):
        op = 0.14 if abs(x) < 0.01 else 0.07
        g.add(
            Line([x, -4, 0], [x, 4, 0], stroke_color=C_GRID, stroke_width=0.9, stroke_opacity=op)
        )
    for y in np.arange(-4.0, 4.1, 0.75):
        op = 0.14 if abs(y) < 0.01 else 0.07
        g.add(
            Line([-7.2, y, 0], [7.2, y, 0], stroke_color=C_GRID, stroke_width=0.9, stroke_opacity=op)
        )
    return g


def _stroke_only(mob: Mobject) -> Mobject:
    mob.set_fill(color=BLACK, opacity=0)
    return mob


def _text_family_ids(root: Mobject) -> set[int]:
    """Text 及其字形子路径 id，禁止对其 set_fill(BLACK)。"""
    ids: set[int] = set()
    for m in root.get_family():
        if isinstance(m, Text):
            for sub in m.get_family():
                ids.add(id(sub))
    return ids


def _stroke_glyph_shapes(glyph: Mobject) -> None:
    """只对非文字几何做描边化，避免黑字。"""
    skip = _text_family_ids(glyph)
    for p in glyph.family_members_with_points():
        if id(p) in skip or isinstance(p, (Dot, Text, Triangle)):
            continue
        _stroke_only(p)


def _restore_glyph_text(glyph: Mobject) -> None:
    """恢复图标内文字为高对比浅色（避免被 stroke_only 染黑）。"""
    for t in glyph.get_family():
        if isinstance(t, Text):
            t.set_color(C_TITLE)
            t.set_fill(C_TITLE, opacity=1)
            t.set_opacity(1)


def _stage_card(name: str, lines: list[str], accent: str, glyph: Mobject, *, key: str = "") -> VGroup:
    """总览卡：不用占位 Rectangle，避免 set_opacity 白底。"""
    fill = RoundedRectangle(
        width=2.55,
        height=3.05,
        corner_radius=0.12,
        fill_color=C_PANEL,
        fill_opacity=0.95,
        stroke_color=accent,
        stroke_width=1.8,
        stroke_opacity=0.9,
    )
    icon_top = fill.get_top()[1] - 0.32
    icon_h = 1.15
    if glyph.width > 1.85:
        glyph.scale_to_fit_width(1.85)
    if glyph.height > icon_h * 0.92:
        glyph.scale_to_fit_height(icon_h * 0.92)
    glyph.move_to([fill.get_center()[0], icon_top - icon_h / 2, 0])

    bar = Line(LEFT * 0.95, RIGHT * 0.95, stroke_color=accent, stroke_width=2.4)
    bar.move_to([fill.get_center()[0], icon_top - icon_h - 0.14, 0])

    title = Text(name, font=UI_FONT, font_size=20, color=accent)
    title.next_to(bar, DOWN, buff=0.16)
    title.set_x(fill.get_center()[0])

    body = VGroup(*[Text(s, font=UI_FONT, font_size=13, color=C_SUB) for s in lines])
    body.arrange(DOWN, buff=0.08, aligned_edge=LEFT)
    body.next_to(title, DOWN, buff=0.14)
    body.set_x(fill.get_center()[0])

    card = VGroup(fill, bar, title, body, glyph)
    card.accent = accent  # type: ignore[attr-defined]
    card.glyph = glyph  # type: ignore[attr-defined]
    card.fill = fill  # type: ignore[attr-defined]
    card.bar = bar  # type: ignore[attr-defined]
    card.title_m = title  # type: ignore[attr-defined]
    card.body_m = body  # type: ignore[attr-defined]
    card.glyph_key = key  # type: ignore[attr-defined]
    return card


def _hide_glyph_parts(glyph: Mobject) -> list[Mobject]:
    def _leaves(mob: Mobject) -> list[Mobject]:
        if isinstance(mob, VGroup) and len(mob) > 0 and not isinstance(mob, Text):
            out: list[Mobject] = []
            for sub in mob:
                out.extend(_leaves(sub))
            return out or [mob]
        return [mob]

    glyph.set_z_index(5)
    parts = _leaves(glyph)
    skip = _text_family_ids(glyph)
    for p in parts:
        if isinstance(p, Text):
            p.set_z_index(6)
            p.set_opacity(0)
            continue
        if id(p) not in skip and not isinstance(p, (Dot, Triangle)):
            _stroke_only(p)
        p.set_z_index(6)
        p.set_opacity(0)
    return parts


def _show_stroke(p: Mobject) -> None:
    if not isinstance(p, (Dot, Text, Triangle)):
        _stroke_only(p)
    p.set_opacity(1)
    p.set_z_index(6)


def _play_glyph_build(scene: Scene, glyph: Mobject, *, key: str = "", run_time: float = 0.7) -> None:
    scene.bring_to_front(glyph)
    parts = _hide_glyph_parts(glyph)
    ease = EASE

    if key == "motive" and len(glyph) >= 4:
        clock, burst, x1, x2 = glyph[0], glyph[1], glyph[2], glyph[3]
        _show_stroke(clock)
        scene.play(GrowFromCenter(clock), run_time=0.28, rate_func=ease)
        _stroke_only(clock)
        scene.play(FadeIn(burst, scale=0.85), run_time=0.22)
        x1.set_opacity(1)
        x2.set_opacity(1)
        scene.play(FadeIn(x1), FadeIn(x2), run_time=0.2)
    elif key == "bake" and len(glyph) >= 4:
        rings, core, heat, label = glyph[0], glyph[1], glyph[2], glyph[3]
        scene.play(FadeIn(core, scale=0.8), run_time=0.12)
        for r in rings:
            _show_stroke(r)
        scene.play(
            LaggedStart(*[GrowFromCenter(r) for r in rings], lag_ratio=0.28),
            run_time=0.5,
            rate_func=ease,
        )
        for r in rings:
            _stroke_only(r)
            r.set_opacity(1)
        heat.set_opacity(1)
        label.set_opacity(1)
        scene.play(FadeIn(heat), FadeIn(label, shift=UP * 0.04), run_time=0.22)
    elif key == "vdata" and len(glyph) >= 4:
        sheet, row_a, row_d, tag = glyph[0], glyph[1], glyph[2], glyph[3]
        _show_stroke(sheet)
        scene.play(FadeIn(sheet, scale=0.96), run_time=0.28, rate_func=ease)
        _stroke_only(sheet)
        row_a.set_opacity(1)
        row_d.set_opacity(1)
        scene.play(FadeIn(row_a, shift=RIGHT * 0.06), FadeIn(row_d, shift=RIGHT * 0.06), run_time=0.28)
        tag.set_opacity(1)
        scene.play(FadeIn(tag, shift=UP * 0.04), run_time=0.16)
    elif key == "runtime" and len(glyph) >= 4:
        table, cursor, flash, o1 = glyph[0], glyph[1], glyph[2], glyph[3]
        _show_stroke(table)
        scene.play(FadeIn(table), run_time=0.22, rate_func=ease)
        _stroke_only(table)
        scene.play(FadeIn(cursor, scale=0.85), run_time=0.18)
        flash.set_opacity(1)
        o1.set_opacity(1)
        scene.play(FadeIn(flash, scale=0.9), FadeIn(o1, shift=UP * 0.05), run_time=0.28)
    else:
        anims = []
        skip = _text_family_ids(glyph)
        for p in parts:
            if isinstance(p, Text) or id(p) in skip:
                p.set_opacity(0)
                anims.append(FadeIn(p, scale=0.92))
                continue
            if not isinstance(p, (Dot, Triangle)):
                _stroke_only(p)
            p.set_opacity(0)
            anims.append(FadeIn(p, scale=0.92))
        scene.play(LaggedStart(*anims, lag_ratio=0.18), run_time=run_time, rate_func=ease)

    skip = _text_family_ids(glyph)
    for p in parts:
        if isinstance(p, Text) or id(p) in skip:
            continue
        if not isinstance(p, (Dot, Triangle)):
            _stroke_only(p)
        p.set_opacity(1)
        p.set_z_index(6)
    _restore_glyph_text(glyph)
    scene.bring_to_front(glyph)


def _glyph_motive() -> VGroup:
    """每帧搜索：时钟 + 爆炸问号被叉掉。"""
    clock = _stroke_only(Circle(radius=0.42, stroke_color=C_HOT, stroke_width=2.0))
    hand = _stroke_only(Line(ORIGIN, UP * 0.28, stroke_color=C_HOT, stroke_width=2.0))
    hand2 = _stroke_only(Line(ORIGIN, RIGHT * 0.18, stroke_color=C_HOT, stroke_width=1.6))
    clock_g = VGroup(clock, hand, hand2)
    burst = VGroup()
    for k in range(6):
        ray = Line(ORIGIN, RIGHT * 0.22, stroke_color=C_WARM, stroke_width=1.6)
        ray.rotate(k * PI / 3, about_point=ORIGIN)
        burst.add(ray)
    burst.shift(RIGHT * 0.55 + UP * 0.05)
    x1 = Line(UL * 0.12, DR * 0.12, stroke_color=C_HOT, stroke_width=2.4)
    x2 = Line(UR * 0.12, DL * 0.12, stroke_color=C_HOT, stroke_width=2.4)
    cross = VGroup(x1, x2).move_to(burst.get_center())
    return VGroup(clock_g, burst, x1, x2)


def _glyph_bake() -> VGroup:
    """Dijkstra 波前外扩。"""
    core = Dot(ORIGIN, radius=0.055, color=C_BAKE)
    rings = VGroup()
    for k in range(3):
        r = Circle(
            radius=0.22 + 0.2 * k,
            stroke_color=C_BAKE,
            stroke_width=1.5,
            stroke_opacity=0.35 + 0.2 * k,
        )
        _stroke_only(r)
        rings.add(r)
    heat = VGroup(
        Dot(RIGHT * 0.28 + UP * 0.18, radius=0.035, color=C_WARM).set_opacity(0.85),
        Dot(LEFT * 0.22 + DOWN * 0.15, radius=0.03, color=C_WARM).set_opacity(0.55),
        Dot(RIGHT * 0.12 + DOWN * 0.28, radius=0.028, color=C_WARM).set_opacity(0.4),
    )
    label = Text("Dijkstra", font="Consolas", font_size=12, color=C_TITLE)
    label.next_to(rings, DOWN, buff=0.08)
    return VGroup(rings, core, heat, label)


def _glyph_vdata() -> VGroup:
    """落盘表：两行字段。"""
    sheet = RoundedRectangle(
        width=1.55,
        height=1.05,
        corner_radius=0.08,
        fill_opacity=0,
        stroke_color=C_SAVE,
        stroke_width=1.8,
    )
    _stroke_only(sheet)
    row_a = Text("arrival", font="Consolas", font_size=13, color=C_SAVE)
    row_d = Text("damage", font="Consolas", font_size=13, color=C_HOT)
    rows = VGroup(row_a, row_d).arrange(DOWN, buff=0.14)
    rows.move_to(sheet.get_center())
    tag = Text(".vdata", font="Consolas", font_size=12, color=C_TITLE)
    tag.next_to(sheet, DOWN, buff=0.08)
    return VGroup(sheet, row_a, row_d, tag)


def _glyph_runtime() -> VGroup:
    """运行时 O(1) 查表。"""
    cells = VGroup()
    for i in range(2):
        for j in range(3):
            c = Square(side_length=0.28, stroke_color=C_PURPLE, stroke_width=1.2, stroke_opacity=0.7)
            _stroke_only(c)
            c.move_to(LEFT * 0.32 + RIGHT * 0.32 * j + UP * 0.18 + DOWN * 0.32 * i)
            cells.add(c)
    cursor = SurroundingRectangle(cells[4], color=C_COOL, buff=0.02, stroke_width=2.2)
    _stroke_only(cursor)
    flash = Dot(cells[4].get_center(), radius=0.05, color=C_COOL)
    o1 = Text("O(1)", font="Consolas", font_size=16, color=C_TITLE)
    o1.next_to(cells, DOWN, buff=0.1)
    return VGroup(cells, cursor, flash, o1)


@dataclass
class PrebakeTitleCardResult:
    """标题卡结束后仍保留 / 待淡出的物件。"""

    title: Mobject
    underline: Mobject
    fade_group: VGroup
    grid: VGroup


def play_prebake_title_card(scene: Scene, *, hold_tail: float = 0.85) -> PrebakeTitleCardResult:
    """播放开场标题 + 预烘焙管线总览。返回可衔接到讲解段的 chrome。"""
    grid = _soft_grid()
    scene.add(grid)

    # 开场：仅橙色点阵由爆心铺开 → Transform 成标题文字
    seed = Dot(ORIGIN, radius=0.075, color=C_BAKE)
    heat = VGroup()
    for i in range(-3, 4):
        for j in range(-2, 3):
            if i == 0 and j == 0:
                continue
            d = (i * i + j * j) ** 0.5
            if d > 3.6:
                continue
            t = d / 3.6
            col = interpolate_color(ManimColor(C_BAKE), ManimColor(C_HOT), min(1.0, t))
            dot = Dot(
                RIGHT * i * 0.42 + UP * j * 0.42,
                radius=0.055 * (1.15 - 0.35 * t),
                color=col,
            )
            dot.set_opacity(0)
            heat.add(dot)
    heat_sorted = sorted(heat, key=lambda m: float(np.linalg.norm(m.get_center()[:2])))
    scene.play(FadeIn(seed, scale=0.35), run_time=0.32, rate_func=EASE)
    scene.play(
        LaggedStart(
            *[
                d.animate.set_opacity(
                    float(np.clip(0.22 + 0.72 * (1 - np.linalg.norm(d.get_center()[:2]) / 2.4), 0.18, 0.95))
                )
                for d in heat_sorted
            ],
            lag_ratio=0.055,
        ),
        run_time=1.15,
        rate_func=EASE,
    )
    scene.wait(0.28)

    title = Text("预烘焙算法", font=UI_FONT, font_size=50, color=C_TITLE)
    title.set_color_by_gradient(C_BAKE, C_SAVE, C_PURPLE)
    underline = Line(LEFT, RIGHT, stroke_color=C_BAKE, stroke_width=2.6)
    underline.set_width(title.width * 0.9)
    en = Text("PREBAKE · SPACE FOR TIME", font="Consolas", font_size=14, color=C_MUTED)
    VGroup(title, underline, en).arrange(DOWN, buff=0.24).move_to(ORIGIN)

    # 点阵向标题区域收束，再整体 Transform 成标题
    all_dots = VGroup(seed, *heat_sorted)
    gather = VGroup(*[d.copy() for d in all_dots])
    n = len(gather)
    for k, d in enumerate(gather):
        u = (k / max(n - 1, 1)) - 0.5
        d.move_to(title.get_center() + RIGHT * (u * title.width * 0.92) + UP * (0.08 * np.sin(k * 1.7)))
        d.set_opacity(0.55)
        d.scale(0.55)
    scene.play(
        LaggedStart(
            *[Transform(src, dst) for src, dst in zip(all_dots, gather)],
            lag_ratio=0.018,
        ),
        run_time=0.85,
        rate_func=EASE,
    )
    scene.play(
        ReplacementTransform(all_dots, title),
        FadeIn(underline, shift=UP * 0.06),
        FadeIn(en, shift=UP * 0.04),
        run_time=0.95,
        rate_func=EASE,
    )
    scene.wait(0.4)

    title_ul = Text("预烘焙算法", font=UI_FONT, font_size=26, color=C_TITLE)
    title_ul.set_color_by_gradient(C_BAKE, C_SAVE)
    title_ul.to_corner(UL, buff=0.42)
    line_ul = Line(ORIGIN, RIGHT * 2.0, stroke_color=C_BAKE, stroke_width=2.2)
    line_ul.next_to(title_ul, DOWN, buff=0.12).align_to(title_ul, LEFT)

    scene.play(
        FadeOut(en),
        Transform(title, title_ul),
        Transform(underline, line_ul),
        run_time=0.85,
        rate_func=EASE,
    )

    lead = Text(
        "编译付一次代价，运行只查表 — 用空间换掉每帧搜索。",
        font=UI_FONT,
        font_size=22,
        color=C_TITLE,
    )
    lead_sub = Text(
        "动机 · Dijkstra 烘焙 · vdata 落盘 · O(1) 查表 — 先建立管线总览。",
        font=UI_FONT,
        font_size=16,
        color=C_SUB,
    )
    lead_block = VGroup(lead, lead_sub).arrange(DOWN, buff=0.14, aligned_edge=LEFT)
    lead_block.next_to(VGroup(title, underline), DOWN, buff=0.36).align_to(title, LEFT)
    if lead_block.get_right()[0] > 6.4:
        lead.set_width(11.5)
        lead_sub.set_width(11.5)
        lead_block.arrange(DOWN, buff=0.14, aligned_edge=LEFT)
        lead_block.next_to(VGroup(title, underline), DOWN, buff=0.36).align_to(title, LEFT)

    scene.play(FadeIn(lead, shift=UP * 0.08), run_time=0.5, rate_func=EASE)
    scene.wait(0.25)
    scene.play(FadeIn(lead_sub, shift=UP * 0.06), run_time=0.4, rate_func=EASE)
    scene.wait(0.3)

    section = Text("四步管线 · 总览", font=UI_FONT, font_size=18, color=C_MUTED)
    section.next_to(lead_block, DOWN, buff=0.28).align_to(lead_block, LEFT)

    cards = VGroup(
        _stage_card("动机", ["每帧 Dijkstra", "玩家 × tick 爆炸"], C_HOT, _glyph_motive(), key="motive"),
        _stage_card("编译烘焙", ["全图走一次", "写出距离场"], C_BAKE, _glyph_bake(), key="bake"),
        _stage_card("落盘", ["arrival + damage", "baked_bomb_damage"], C_SAVE, _glyph_vdata(), key="vdata"),
        _stage_card("运行查表", ["读格即得", "零路径搜索"], C_PURPLE, _glyph_runtime(), key="runtime"),
    ).arrange(RIGHT, buff=0.28)

    bar_y = cards[0].bar.get_center()[1]
    for card in cards:
        dy = bar_y - card.bar.get_center()[1]
        card.bar.shift(UP * dy)
        card.title_m.shift(UP * dy)
        card.body_m.shift(UP * dy)

    top_y = section.get_bottom()[1] - 0.22
    bot_y = -3.45
    cards.move_to([0, (top_y + bot_y) / 2, 0])

    bar_y = cards[0].bar.get_center()[1]
    for card in cards:
        dy = bar_y - card.bar.get_center()[1]
        card.bar.shift(UP * dy)
        card.title_m.shift(UP * dy)
        card.body_m.shift(UP * dy)

    arrows = VGroup()
    for i in range(len(cards) - 1):
        a = Arrow(
            cards[i].get_right() + RIGHT * 0.02,
            cards[i + 1].get_left() + LEFT * 0.02,
            buff=0.02,
            stroke_width=1.4,
            color="#2e3a4e",
            max_tip_length_to_length_ratio=0.35,
            tip_length=0.1,
        )
        a.set_opacity(0.7)
        arrows.add(a)

    scene.play(FadeIn(section, shift=UP * 0.06), run_time=0.3, rate_func=EASE)

    for card in cards:
        card.bar.set_opacity(0)
        card.title_m.set_opacity(0)
        card.body_m.set_opacity(0)
        _stroke_glyph_shapes(card.glyph)
        for p in card.glyph.family_members_with_points():
            if id(p) in _text_family_ids(card.glyph) or isinstance(p, (Dot, Text, Triangle)):
                p.set_opacity(0)
                continue
            p.set_opacity(0)
        # Text 整体透明度
        for t in card.glyph.get_family():
            if isinstance(t, Text):
                t.set_opacity(0)
        card.fill.set_opacity(0)

    for card in cards:
        card.fill.set_opacity(1)
        scene.play(FadeIn(card.fill, scale=0.97), run_time=0.28, rate_func=EASE)
        scene.bring_to_front(card.glyph)
        _play_glyph_build(scene, card.glyph, key=getattr(card, "glyph_key", ""), run_time=0.55)
        card.bar.set_opacity(1)
        card.title_m.set_opacity(1)
        card.body_m.set_opacity(1)
        scene.play(
            FadeIn(card.bar),
            Write(card.title_m),
            LaggedStart(*[Write(line) for line in card.body_m], lag_ratio=0.12),
            run_time=0.5,
            rate_func=EASE,
        )
        scene.bring_to_front(card.glyph)
        scene.play(card.fill.animate.set_stroke(width=3.2), run_time=0.18, rate_func=EASE)
        scene.play(card.fill.animate.set_stroke(width=1.8), run_time=0.14, rate_func=EASE)

    for card in cards:
        card.fill.set_fill(C_PANEL, opacity=0.95)
        card.fill.set_stroke(color=card.accent, width=1.8, opacity=0.9)
        _stroke_glyph_shapes(card.glyph)
        skip = _text_family_ids(card.glyph)
        for p in card.glyph.family_members_with_points():
            if id(p) in skip or isinstance(p, (Dot, Text, Triangle)):
                continue
            p.set_opacity(1)
        _restore_glyph_text(card.glyph)
        scene.bring_to_front(card.glyph)

    scene.play(
        LaggedStart(*[FadeIn(a, scale=0.85) for a in arrows], lag_ratio=0.1),
        run_time=0.35,
    )
    scene.wait(hold_tail)

    fade_group = VGroup(lead, lead_sub, section, cards, arrows)
    return PrebakeTitleCardResult(title=title, underline=underline, fade_group=fade_group, grid=grid)


class PrebakeTitleScene(Scene):
    """预烘焙算法 · 标题卡（文主图辅，风格对齐 02 搜索算法 title）。"""

    def construct(self):
        self.camera.background_color = ManimColor(C_BG)
        play_prebake_title_card(self, hold_tail=1.4)
