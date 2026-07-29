# rainbow_yu — CS2 C4 成片：冲击波算法与三维对比
"""球体穿墙 vs 路径波前；含 2D 讲解与 3D 竞技场对比。

Usage:
    python -m manim -qh video_project/cs2_c4/manim/shockwave.py ShockwaveAlgorithmScene
    python -m manim -qh video_project/cs2_c4/manim/shockwave.py OldBombSphere3DScene
    python -m manim -qh video_project/cs2_c4/manim/shockwave.py NewBombSearch3DScene
"""

from __future__ import annotations

import numpy as np
from manim import *

from yty_manim.basic_unit.cs2_arena import *  # noqa: F401,F403
from yty_manim.basic_unit.cs2_map import WAVE_SPEED_M_S
from yty_manim.disposition.fonts_and_colors import text_font

__all__ = (
    "ShockwaveAlgorithmScene",
    "OldBombSphere3DScene",
    "NewBombSearch3DScene",
)


# ── 冲击波算法讲解 ──────────────────────────────────────────

from yty_manim.basic_unit.cs2_arena import (
    CELL_2D as CELL,
    MAP_SCALE,
    MAP_SHIFT,
    FormulaLine,
    GridMap2D,
    _heat_color,
    _ij_to_xy,
    _layers_from_dist,
    _path_mobject,
)
C_BG = "#06080f"
C_TITLE = "#eef2ff"
C_SUB = "#94a3b8"
C_HOT = "#ff6b4a"
C_WARM = "#f0a040"
C_COOL = "#3de0c8"
C_BAD = "#ff6b6b"
C_GOOD = "#4ade80"
C_PANEL = "#0e1420"
C_PANEL_EDGE = "#2a3a55"
C_OLD = "#ff4d4d"

MAP_T = MAP_SCALE * 0.82
MAP_O = MAP_SHIFT + LEFT * 0.55 + DOWN * 0.08
RIGHT_BUFF = 0.72
CAPTION_Y = -3.15
FRAME_RIGHT = 6.55
Z_H, Z_C, Z_P, Z_M, Z_K = 20, 20, 12, 4, 14

RT_H, RT_C, RT_F, RT_S = 0.75, 0.6, 0.7, 0.95
W_S, W_M, W_L = 1.1, 1.6, 2.2


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
CODE = "Consolas"


def _euclid_dist(start: tuple[int, int]) -> np.ndarray:
    h, w = GRID.shape
    si, sj = start
    out = np.full((h, w), np.inf)
    for i in range(h):
        for j in range(w):
            if GRID[i, j]:
                out[i, j] = float(np.hypot(i - si, j - sj))
    return out


def _header(step: str, title: str, accent: str = C_TITLE) -> VGroup:
    badge = RoundedRectangle(
        width=0.62,
        height=0.36,
        corner_radius=0.07,
        fill_color=accent,
        fill_opacity=0.2,
        stroke_color=accent,
        stroke_width=1.2,
    )
    bl = Text(step, font=UI_FONT, font_size=16, color=accent).move_to(badge)
    hdr = Text(title, font=UI_FONT, font_size=26, color=ManimColor(C_TITLE))
    g = VGroup(VGroup(badge, bl), hdr).arrange(RIGHT, buff=0.18, aligned_edge=DOWN)
    g.to_edge(UP, buff=0.32).set_z_index(Z_H)
    return g


def _caption(text: str, color: str = C_SUB) -> Text:
    cap = Text(text, font=UI_FONT, font_size=16, color=color, line_spacing=0.95)
    if cap.width > 12.0:
        cap.set_width(12.0)
    return cap.move_to([0, CAPTION_Y, 0]).set_z_index(Z_C)


def _card(title: str, lines: list[str], accent: str, width: float = 4.0) -> VGroup:
    t = Text(title, font=UI_FONT, font_size=17, color=ManimColor(accent))
    body = VGroup(*[Text(ln, font=UI_FONT, font_size=14, color="#d8e2f0") for ln in lines])
    body.arrange(DOWN, buff=0.08, aligned_edge=LEFT)
    content = VGroup(t, body).arrange(DOWN, buff=0.12, aligned_edge=LEFT)
    box = RoundedRectangle(
        width=max(content.width + 0.64, width),
        height=content.height + 0.5,
        corner_radius=0.12,
        fill_color=C_PANEL,
        fill_opacity=0.95,
        stroke_color=C_PANEL_EDGE,
        stroke_width=1.2,
    )
    content.move_to(box)
    return VGroup(box, content).set_z_index(Z_P)


def _mono(s: str, size: int = 15, color: str = WHITE) -> Text:
    return Text(s, font=CODE, font_size=size, color=color)


def _formula(line: FormulaLine, size: int = 20, color: str = WHITE) -> Mobject:
    try:
        return MathTex(line.math, font_size=size + 4, color=color)
    except Exception:
        return _mono(line.display, size=size, color=color)


def _place_map(g: GridMap2D) -> None:
    g.apply_map_transform(MAP_T, MAP_O)
    g.set_z_index(Z_M)
    g.markers.set_z_index(Z_K)


def _place_right(panel: Mobject, map_body: Mobject) -> Mobject:
    panel.next_to(map_body, RIGHT, buff=RIGHT_BUFF)
    panel.align_to(map_body, UP).shift(DOWN * 0.06)
    if panel.get_right()[0] > FRAME_RIGHT:
        panel.shift(LEFT * (panel.get_right()[0] - FRAME_RIGHT + 0.1))
    if panel.get_bottom()[1] < CAPTION_Y + 0.5:
        panel.shift(UP * (CAPTION_Y + 0.5 - panel.get_bottom()[1]))
    return panel.set_z_index(Z_P)


def _paint(grid: GridMap2D, dist: np.ndarray, max_d: float, i: int, j: int) -> None:
    if not np.isfinite(dist[i, j]) or max_d <= 0:
        return
    t = float(np.clip(1.0 - dist[i, j] / max_d, 0, 1))
    grid.tiles[(i, j)].set_fill(_heat_color(0.2 + 0.8 * t), opacity=1)


class ShockwaveAlgorithmScene(Scene):
    """冲击波算法完整讲解：旧球 → 路径波 → 到达结算。"""

    def construct(self):
        self.camera.background_color = ManimColor(C_BG)

        start, goal = BOMB_IJ, SURVIVOR_IJ
        path_dist = _bfs_dist(start)
        euc_dist = _euclid_dist(start)
        path = _bfs_path(start, goal)
        layers = _layers_from_dist(path_dist)
        finite = path_dist[np.isfinite(path_dist)]
        max_pd = float(finite.max()) if finite.size else 1.0
        max_ed = float(euc_dist[np.isfinite(euc_dist)].max()) if np.any(np.isfinite(euc_dist)) else 1.0
        pd_goal = float(path_dist[goal])
        ed_goal = float(euc_dist[goal])
        # 玩具格：按社区标定速度换算示意到达时间（格距≈0.625m 量级）
        arrival_s = pd_goal * 0.625 / WAVE_SPEED_M_S

        header: Mobject | None = None
        caption: Mobject | None = None

        def set_header(step: str, title: str, accent: str = C_TITLE) -> Mobject:
            nonlocal header
            new = _header(step, title, accent)
            if header is None:
                self.play(FadeIn(new), run_time=RT_H, rate_func=smooth)
            else:
                self.play(ReplacementTransform(header, new), run_time=RT_H, rate_func=smooth)
            header = new
            return new

        def set_caption(text: str, color: str = C_SUB) -> Mobject:
            nonlocal caption
            new = _caption(text, color)
            if caption is None:
                self.play(FadeIn(new), run_time=RT_C, rate_func=smooth)
            else:
                self.play(ReplacementTransform(caption, new), run_time=RT_C, rate_func=smooth)
            caption = new
            return new

        # ══════════════════════════════════════════════════════════════
        # 0 · 开场
        # ══════════════════════════════════════════════════════════════
        hero_t = Text("冲击波算法", font=UI_FONT, font_size=40, color=ManimColor(C_TITLE))
        hero_t.set_color_by_gradient(C_HOT, C_WARM, C_COOL)
        hero_s = Text(
            "Season 5 · 从欧氏球体到路径波前",
            font=UI_FONT,
            font_size=18,
            color=C_SUB,
        )
        hero = VGroup(hero_t, hero_s).arrange(DOWN, buff=0.2)
        self.play(FadeIn(hero, shift=UP * 0.1), run_time=RT_F, rate_func=smooth)
        self.wait(W_M)
        self.play(FadeOut(hero), run_time=0.4)

        # ══════════════════════════════════════════════════════════════
        # 1 · 机制变化
        # ══════════════════════════════════════════════════════════════
        set_header("01", "Season 5 改了什么？", C_HOT)
        set_caption("官方：伤害按预计算模拟值结算，冲击波从爆心向外扩展")

        old_c = _card(
            "旧机制（近似）",
            [
                "按直线距离 / 半径球结算",
                "墙体几乎不挡 → 穿墙满伤",
                "选手凭经验猜「能不能活」",
            ],
            C_OLD,
            width=4.3,
        )
        new_c = _card(
            "新机制（官方）",
            [
                "冲击波沿地图几何蔓延",
                "墙几乎阻断 · 拐角大幅衰减",
                "波前到达才扣血 · 血条可预览",
            ],
            C_COOL,
            width=4.3,
        )
        duo = VGroup(old_c, new_c).arrange(RIGHT, buff=0.55).shift(DOWN * 0.15)
        duo.scale_to_fit_width(11.2)
        self.play(FadeIn(old_c, shift=UP * 0.08), run_time=RT_F, rate_func=smooth)
        self.wait(W_S)
        self.play(FadeIn(new_c, shift=UP * 0.08), run_time=RT_F, rate_func=smooth)
        self.wait(W_L)
        self.play(FadeOut(duo), run_time=0.45)

        # ══════════════════════════════════════════════════════════════
        # 2 · 旧模型：欧氏球穿墙
        # ══════════════════════════════════════════════════════════════
        set_header("02", "旧模型：欧氏半径球", C_OLD)
        set_caption("直线距离 ≤ R 就受伤 — 墙后玩家也会被算进球里")

        grid = GridMap2D(start, goal)
        _place_map(grid)
        self.play(FadeIn(grid), FadeIn(grid.markers), run_time=RT_S, rate_func=smooth)

        bomb_c = grid.tiles[start].get_center()
        r_tracker = ValueTracker(0.0)
        sphere = always_redraw(
            lambda: Circle(
                radius=max(r_tracker.get_value(), 0.01),
                stroke_color=C_OLD,
                stroke_width=2.4,
                stroke_opacity=0.9,
            )
            .move_to(bomb_c)
            .set_fill(C_OLD, opacity=0.12)
        )
        old_panel = _card(
            "欧氏判定",
            [
                "dist = √(Δx² + Δy²)",
                "if dist ≤ R → 受伤",
                "不感知墙体 / 走廊",
            ],
            C_OLD,
            width=3.9,
        )
        _place_right(old_panel, grid)
        self.add(sphere)
        self.play(FadeIn(old_panel, shift=LEFT * 0.1), run_time=RT_F, rate_func=smooth)

        target_r = ed_goal * CELL * MAP_T + 0.08
        # 随半径给球内格子染色
        def _paint_euc(mob=None):
            r_cells = r_tracker.get_value() / (CELL * MAP_T + 1e-6)
            for (i, j), tile in grid.tiles.items():
                d = euc_dist[i, j]
                if np.isfinite(d) and d <= r_cells:
                    t = float(np.clip(1.0 - d / max(max_ed, 1e-6), 0, 1))
                    tile.set_fill(_heat_color(0.25 + 0.75 * t), opacity=1)
                else:
                    tile.set_fill("#1c2838", opacity=1)

        grid.add_updater(_paint_euc)
        self.play(r_tracker.animate.set_value(target_r), run_time=3.2, rate_func=smooth)
        grid.remove_updater(_paint_euc)
        _paint_euc()

        hit = Text(
            f"墙后玩家 · 欧氏 {ed_goal:.1f} 格 → 仍被击中",
            font=UI_FONT,
            font_size=15,
            color=C_BAD,
        )
        hit.next_to(old_panel, DOWN, buff=0.28).align_to(old_panel, LEFT)
        self.play(FadeIn(hit), run_time=RT_F, rate_func=smooth)
        set_caption("问题：几何上「近」，但中间隔着墙 — 旧模型仍判致命")
        self.wait(W_L)

        self.play(FadeOut(sphere), FadeOut(old_panel), FadeOut(hit), run_time=0.45)
        grid.reset_tiles()

        # ══════════════════════════════════════════════════════════════
        # 3 · 新模型：路径波前
        # ══════════════════════════════════════════════════════════════
        set_header("03", "新模型：沿可走格扩散的波前", C_COOL)
        set_caption("冲击波只能走地板 — 墙挡住就绕路，绕不过就到不了")

        new_panel = _card(
            "路径波前",
            [
                "从包点做网格搜索",
                "4/8 连通邻域外扩",
                "墙格不可进入 → 自然绕行",
            ],
            C_COOL,
            width=3.9,
        )
        _place_right(new_panel, grid)
        self.play(FadeIn(new_panel, shift=LEFT * 0.1), run_time=RT_F, rate_func=smooth)

        # 分层染色 = BFS 波前
        for li, layer in enumerate(layers):
            anims = []
            for i, j in layer:
                t = float(np.clip(1.0 - path_dist[i, j] / max_pd, 0, 1))
                anims.append(
                    grid.tiles[(i, j)].animate.set_fill(_heat_color(0.2 + 0.8 * t), opacity=1)
                )
            if anims:
                self.play(*anims, run_time=0.32 if li < 5 else 0.18, rate_func=smooth)

        set_caption("颜色越暖 = 路径越短 / 伤害越高；波前像水漫过地图")
        self.wait(W_M + 0.4)

        # 最短路径描线
        path_mob = _path_mobject(path, color=C_COOL, scale=MAP_T, shift=MAP_O)
        self.play(Create(path_mob), run_time=1.4, rate_func=smooth)
        cmp = Text(
            f"路径 {pd_goal:.0f} 格  ≫  欧氏 {ed_goal:.1f} 格",
            font=UI_FONT,
            font_size=15,
            color=C_WARM,
        )
        cmp.next_to(new_panel, DOWN, buff=0.28).align_to(new_panel, LEFT)
        self.play(FadeIn(cmp), run_time=RT_F, rate_func=smooth)
        set_caption("同一玩家：直线很近，但绕墙路径很长 → 伤害被大幅削弱")
        self.wait(W_L)

        # 对照表：同一位置两种模型
        self.play(FadeOut(path_mob), FadeOut(cmp), FadeOut(new_panel), run_time=0.4)
        compare = VGroup(
            _card(
                "欧氏模型",
                [
                    f"距离 {ed_goal:.1f} 格（穿墙直线）",
                    "判定：在球内 → 高伤",
                    "公平性：差（墙形同虚设）",
                ],
                C_OLD,
                width=4.4,
            ),
            _card(
                "路径波模型",
                [
                    f"距离 {pd_goal:.0f} 格（绕墙最短路）",
                    "判定：波前到达才结算",
                    "公平性：好（尊重地图几何）",
                ],
                C_COOL,
                width=4.4,
            ),
        ).arrange(RIGHT, buff=0.5).shift(DOWN * 0.1)
        # 暂时藏地图信息，突出对照
        self.play(
            grid.animate.set_opacity(0.25),
            grid.markers.animate.set_opacity(0.25),
            run_time=0.45,
        )
        self.play(FadeIn(compare, shift=UP * 0.08), run_time=RT_F, rate_func=smooth)
        set_caption("算法换的不是「爆炸特效」，而是「伤害如何尊重墙与走廊」")
        self.wait(W_L + 0.3)
        self.play(
            FadeOut(compare),
            grid.animate.set_opacity(1),
            grid.markers.animate.set_opacity(1),
            run_time=0.5,
        )
        grid.reset_tiles()
        # 恢复热力场供后续
        for (i, j), tile in grid.tiles.items():
            if np.isfinite(path_dist[i, j]):
                _paint(grid, path_dist, max_pd, i, j)

        # ══════════════════════════════════════════════════════════════
        # 4 · 算法本质：距离场
        # ══════════════════════════════════════════════════════════════
        set_header("04", "算法本质：最短路径距离场", C_WARM)
        set_caption("【推断】烘焙阶段对每格求 Dijkstra/BFS 最短路径距离")

        algo_panel = VGroup(
            Text("核心量", font=UI_FONT, font_size=17, color=C_WARM),
            _formula(
                FormulaLine(
                    r"d(c)=\mathrm{ShortestPath}(\mathrm{site},\,c)",
                    "d(c) = ShortestPath(site, c)",
                ),
                size=18,
                color=C_TITLE,
            ),
            Text("受墙约束 · 可走格连通", font=UI_FONT, font_size=13, color=C_SUB),
            Text("常用实现", font=UI_FONT, font_size=17, color=C_COOL),
            Text("· BFS（等权格）", font=UI_FONT, font_size=14, color="#d8e2f0"),
            Text("· Dijkstra（拐角加权）", font=UI_FONT, font_size=14, color="#d8e2f0"),
            Text("输出", font=UI_FONT, font_size=17, color=C_HOT),
            Text("每格一张「距离场」热力图", font=UI_FONT, font_size=14, color="#d8e2f0"),
        ).arrange(DOWN, buff=0.14, aligned_edge=LEFT)
        box = RoundedRectangle(
            width=algo_panel.width + 0.7,
            height=algo_panel.height + 0.55,
            corner_radius=0.12,
            fill_color=C_PANEL,
            fill_opacity=0.95,
            stroke_color=C_PANEL_EDGE,
        )
        algo_panel.move_to(box)
        algo_card = VGroup(box, algo_panel)
        _place_right(algo_card, grid)
        self.play(FadeIn(algo_card, shift=LEFT * 0.1), run_time=RT_F, rate_func=smooth)
        self.wait(W_L)

        # ══════════════════════════════════════════════════════════════
        # 5 · 到达时间与伤害
        # ══════════════════════════════════════════════════════════════
        set_header("05", "到达时间与伤害衰减", C_HOT)
        set_caption(f"社区标定 WAVE_SPEED ≈ {WAVE_SPEED_M_S} m/s · 越远越弱，拐角再衰减")

        self.play(FadeOut(algo_card), run_time=0.35)
        form_panel = VGroup(
            Text("到达时刻", font=UI_FONT, font_size=17, color=C_COOL),
            _formula(
                FormulaLine(
                    rf"\mathrm{{arrival}}=\frac{{d\cdot \Delta}}{{{WAVE_SPEED_M_S}\,\mathrm{{m/s}}}}",
                    f"arrival = d × 格距 / {WAVE_SPEED_M_S} m/s",
                ),
                size=17,
                color=C_TITLE,
            ),
            Text(f"本例墙后玩家 ≈ {arrival_s:.2f} s", font=UI_FONT, font_size=14, color=C_WARM),
            Text("伤害功率", font=UI_FONT, font_size=17, color=C_HOT),
            _formula(
                FormulaLine(
                    r"\mathrm{damage}=\mathrm{Falloff}(d,\,\mathrm{corners})",
                    "damage = Falloff(d, corners)",
                ),
                size=16,
                color=C_TITLE,
            ),
            Text("致命区约 33–77 m 波程（社区）", font=UI_FONT, font_size=13, color=C_SUB),
            Text("护甲不减免炸弹伤害（实测）", font=UI_FONT, font_size=13, color=C_SUB),
        ).arrange(DOWN, buff=0.14, aligned_edge=LEFT)
        fbox = RoundedRectangle(
            width=form_panel.width + 0.7,
            height=form_panel.height + 0.55,
            corner_radius=0.12,
            fill_color=C_PANEL,
            fill_opacity=0.95,
            stroke_color=C_PANEL_EDGE,
        )
        form_panel.move_to(fbox)
        form_card = VGroup(fbox, form_panel)
        _place_right(form_card, grid)
        self.play(FadeIn(form_card, shift=LEFT * 0.1), run_time=RT_F, rate_func=smooth)
        self.wait(W_L)

        # ══════════════════════════════════════════════════════════════
        # 6 · 运行时结算
        # ══════════════════════════════════════════════════════════════
        set_header("06", "运行时：波前推进 + 查表", C_GOOD)
        set_caption("比赛时不再搜路 — 只推进波前半径，读预计算表")

        self.play(FadeOut(form_card), run_time=0.35)
        steps = VGroup(
            *[
                _card(t, [b], a, width=3.85)
                for (t, b, a) in (
                    ("① 波前", "wave = t0 + (t−t0)×SPEED", C_COOL),
                    ("② 查表", "读 arrival / damage_power", C_WARM),
                    ("③ 结算", "wave ≥ arrival → 扣血", C_HOT),
                )
            ]
        ).arrange(DOWN, buff=0.22)
        _place_right(steps, grid)
        for s in steps:
            self.play(FadeIn(s, shift=LEFT * 0.08), run_time=0.45, rate_func=smooth)
            self.wait(0.35)

        # ValueTracker 波前扫到玩家
        grid.reset_tiles()
        wave_t = ValueTracker(0.0)

        def _paint_wave(_=None):
            r = wave_t.get_value()
            for (i, j), tile in grid.tiles.items():
                d = path_dist[i, j]
                if np.isfinite(d) and d <= r:
                    t = float(np.clip(1.0 - d / max_pd, 0, 1))
                    tile.set_fill(_heat_color(0.2 + 0.8 * t), opacity=1)
                else:
                    tile.set_fill("#1c2838", opacity=1)

        grid.add_updater(_paint_wave)
        self.play(wave_t.animate.set_value(pd_goal + 0.3), run_time=3.4, rate_func=smooth)
        grid.remove_updater(_paint_wave)
        _paint_wave()
        flash = Text("波前到达 → ApplyDamage", font=UI_FONT, font_size=15, color=C_HOT)
        flash.next_to(steps, DOWN, buff=0.22).align_to(steps, LEFT)
        self.play(
            FadeIn(flash),
            Flash(grid.tiles[goal], color=C_HOT, line_length=0.25, num_lines=10, flash_radius=0.4),
            run_time=0.7,
        )
        set_caption("血条预览读同一张表：preview = HP − damage_power")
        self.wait(W_L)

        self.play(
            FadeOut(steps),
            FadeOut(flash),
            FadeOut(grid),
            FadeOut(grid.markers),
            run_time=0.5,
        )

        # ══════════════════════════════════════════════════════════════
        # 7 · 小结
        # ══════════════════════════════════════════════════════════════
        set_header("07", "一句话抓住本质", C_TITLE)
        set_caption("编译时算路径距离场 · 运行时只推波前、查表扣血")

        points = VGroup(
            _card("① 几何", ["不是欧氏球", "是沿 nav 的路径波"], C_OLD, width=3.5),
            _card("② 场", ["每格 shortest path", "墙阻断 · 拐角衰减"], C_WARM, width=3.5),
            _card("③ 时间", ["arrival = d / SPEED", "到达才结算"], C_COOL, width=3.5),
            _card("④ 工程", ["烘焙进 vdata", "运行 O(1) 查表"], C_GOOD, width=3.5),
        ).arrange_in_grid(rows=2, cols=2, buff=(0.4, 0.35))
        points.move_to(ORIGIN + DOWN * 0.15)
        for p in points:
            self.play(FadeIn(p, shift=UP * 0.06), run_time=0.4, rate_func=smooth)
        self.wait(W_L)

        closer = Text(
            "公平来自几何，性能来自预计算",
            font=UI_FONT,
            font_size=22,
            color=ManimColor(C_TITLE),
        )
        closer.next_to(points, DOWN, buff=0.45)
        self.play(FadeIn(closer), run_time=RT_F, rate_func=smooth)
        self.wait(W_L + 0.4)

# ── 三维球体 vs 路径波 ──────────────────────────────────────

class OldBombSphere3DScene(ThreeDScene):
    """旧机制：欧氏距离球体扩展，穿墙同等伤害。"""

    def construct(self):
        self.camera.background_color = ManimColor(BG)
        self.set_camera_orientation(phi=58 * DEGREES, theta=-55 * DEGREES, zoom=0.72)

        title = _hud_title("旧机制 · 球体爆炸", "欧氏距离 · 穿墙同伤", ACCENT_OLD)
        title.to_corner(UL, buff=0.32)
        self.add_fixed_in_frame_mobjects(title)
        self.play(FadeIn(title, shift=UP * 0.12), run_time=0.7)

        arena = Arena3D()
        self.play(FadeIn(arena, shift=OUT * 0.2), run_time=1.3)
        self.wait(0.25)

        bomb_pos = _cell_to_xyz(*BOMB_IJ, z=FLOOR_H + 0.3)
        surv_pos = _cell_to_xyz(*SURVIVOR_IJ, z=FLOOR_H + 0.3)
        hit_r = float(np.linalg.norm(surv_pos[:2] - bomb_pos[:2])) + 0.55
        max_r = hit_r + 1.4
        # Euclidean damage falloff radius (for color): map distance → intensity
        dmg_max = max_r * 1.05

        radius = ValueTracker(0.12)
        shell_holder = VGroup()
        self.add(shell_holder)

        def refresh_shell(mob=None, dt=0):
            r = max(radius.get_value(), 0.08)
            t_edge = float(np.clip(1.0 - r / dmg_max, 0.15, 1.0))
            col = _damage_color(max(t_edge, 0.55))
            shell_holder.remove(*shell_holder)
            shell_holder.add(_wire_sphere(r, col, bomb_pos, n_lat=9, n_lon=10))

        def update_tiles(mob=None, dt=0):
            r = radius.get_value()
            for (i, j), tile in arena.floor_cells.items():
                p = _cell_to_xyz(i, j)
                d = float(np.linalg.norm(p[:2] - bomb_pos[:2]))
                if d <= r:
                    # Damage intensity from Euclidean distance (independent of wall)
                    t = float(np.clip(1.0 - d / dmg_max, 0.0, 1.0))
                    _set_tile_color(tile, _damage_color(t))
                else:
                    _set_tile_color(tile, FLOOR)

        arena.add_updater(update_tiles)
        shell_holder.add_updater(refresh_shell)

        self.play(
            arena.bomb.animate.set_fill(ManimColor("#ffffff"), opacity=1).scale(1.3),
            run_time=0.4,
        )
        self.play(
            arena.bomb.animate.set_fill(ManimColor(BOMB_GLOW), opacity=1).scale(1 / 1.3),
            run_time=0.22,
        )

        label = Text("球体无视墙体 · 拐角同伤", font=UI_FONT, font_size=20, color=ManimColor(ACCENT_OLD))
        label.to_corner(DR, buff=0.35)
        self.add_fixed_in_frame_mobjects(label)
        self.play(FadeIn(label), run_time=0.35)

        # Smooth orbit during expansion (manual theta — more stable than ambient + redraw)
        self.move_camera(
            theta=-55 * DEGREES + 0.95,
            phi=56 * DEGREES,
            run_time=5.8,
            rate_func=smooth,
            added_anims=[radius.animate.set_value(max_r)],
        )

        self.play(arena.survivor.animate.set_color(ManimColor(ACCENT_OLD)), run_time=0.55)
        dmg = Text("致死伤害（穿墙未衰减）", font=UI_FONT, font_size=22, color=ManimColor(ACCENT_OLD))
        dmg.next_to(label, UP, buff=0.12)
        self.add_fixed_in_frame_mobjects(dmg)
        self.play(FadeIn(dmg, shift=UP * 0.08), run_time=0.45)

        self.wait(1.4)
        arena.remove_updater(update_tiles)
        shell_holder.remove_updater(refresh_shell)
        self.wait(0.4)


# ── Scene: New BFS search wave ───────────────────────────────────────────────
class NewBombSearch3DScene(ThreeDScene):
    """新机制：BFS 路径搜索冲击波，绕墙传播。"""

    def construct(self):
        self.camera.background_color = ManimColor(BG)
        self.set_camera_orientation(phi=58 * DEGREES, theta=-55 * DEGREES, zoom=0.72)

        title = _hud_title("新机制 · 搜索冲击波", "BFS 路径传播 · 绕墙衰减", ACCENT_NEW)
        title.to_corner(UL, buff=0.32)
        self.add_fixed_in_frame_mobjects(title)
        self.play(FadeIn(title, shift=UP * 0.12), run_time=0.7)

        arena = Arena3D()
        self.play(FadeIn(arena, shift=OUT * 0.2), run_time=1.3)

        dist = _bfs_dist(BOMB_IJ)
        path = _bfs_path(BOMB_IJ, SURVIVOR_IJ)
        finite = dist[np.isfinite(dist)]
        max_d = float(np.max(finite)) if finite.size else 1.0
        # Falloff slightly longer than map so far cells still get cool tint
        dmg_max = max_d * 1.05
        inten = _intensity_from_dist(dist, max_r=dmg_max)

        eucl = float(
            np.linalg.norm(
                _cell_to_xyz(*SURVIVOR_IJ)[:2] - _cell_to_xyz(*BOMB_IJ)[:2]
            )
            / CELL
        )
        path_len = dist[SURVIVOR_IJ]

        # Ghost Euclidean ring (shows "through-wall" radius vs path)
        ghost_r = float(np.linalg.norm(
            _cell_to_xyz(*SURVIVOR_IJ)[:2] - _cell_to_xyz(*BOMB_IJ)[:2]
        ))
        ghost = Circle(radius=ghost_r, color=ManimColor("#ff4d4d"), stroke_width=2)
        ghost.set_stroke(opacity=0.35)
        ghost.move_to(_cell_to_xyz(*BOMB_IJ, z=FLOOR_H + 0.04))
        ghost_lbl = Text(
            f"欧氏 ≈ {eucl:.0f} 格",
            font=UI_FONT,
            font_size=16,
            color=ManimColor(ACCENT_OLD),
        )
        ghost_lbl.to_corner(DL, buff=0.35)
        self.add_fixed_in_frame_mobjects(ghost_lbl)
        self.play(Create(ghost), FadeIn(ghost_lbl), run_time=0.7)

        # Path ribbon on floor (algorithm route)
        path_dots = VGroup()
        for idx, (i, j) in enumerate(path):
            p = _cell_to_xyz(i, j, z=FLOOR_H + 0.08)
            d = Dot(point=p, radius=0.06, color=ManimColor(ACCENT_NEW))
            d.set_shade_in_3d(False)
            path_dots.add(d)
        path_line = VGroup()
        for a, b in zip(path, path[1:]):
            pa = _cell_to_xyz(*a, z=FLOOR_H + 0.09)
            pb = _cell_to_xyz(*b, z=FLOOR_H + 0.09)
            seg = Line(pa, pb, color=ManimColor(ACCENT_NEW), stroke_width=3.5)
            seg.set_stroke(opacity=0.75)
            path_line.add(seg)

        wave_r = ValueTracker(0.0)
        frontier = VGroup()
        self.add(frontier)

        def refresh_wave(mob=None, dt=0):
            r = wave_r.get_value()
            frontier_pts = []
            for (i, j), tile in arena.floor_cells.items():
                d = dist[i, j]
                if not np.isfinite(d):
                    continue
                c = _cell_to_xyz(i, j)
                if d <= r:
                    t = float(inten[i, j])
                    _set_tile_color(tile, _damage_color(t))
                    # Mild lift at the wave front
                    lift = 0.12 * max(0.0, 1.0 - abs(d - r) * 0.55)
                    tile.move_to([c[0], c[1], FLOOR_H + lift])
                    if abs(d - r) < 0.9:
                        frontier_pts.append(_cell_to_xyz(i, j, z=FLOOR_H + 0.28 + 0.12 * t))
                else:
                    _set_tile_color(tile, FLOOR)
                    tile.move_to([c[0], c[1], FLOOR_H])

            frontier.remove(*frontier)
            sparks = VGroup()
            for p in frontier_pts[:48]:
                spark = Sphere(radius=0.055, resolution=(5, 5))
                spark.set_fill(ManimColor("#fff7ed"), opacity=0.9).set_stroke(width=0)
                spark.set_shade_in_3d(False)
                spark.move_to(p)
                sparks.add(spark)
            if len(sparks):
                frontier.add(*sparks)

        self.play(
            arena.bomb.animate.set_fill(ManimColor("#ffffff"), opacity=1).scale(1.3),
            run_time=0.4,
        )
        self.play(
            arena.bomb.animate.set_fill(ManimColor(BOMB_GLOW), opacity=1).scale(1 / 1.3),
            run_time=0.22,
        )

        hint = Text(
            "广度优先 · 只沿可走格扩展（不穿墙）",
            font=UI_FONT,
            font_size=20,
            color=ManimColor(ACCENT_NEW),
        )
        hint.to_corner(DR, buff=0.35)
        self.add_fixed_in_frame_mobjects(hint)
        self.play(FadeIn(hint), FadeIn(path_dots), Create(path_line), run_time=0.85)

        # Algorithm preview: expand first few distance rings cell-by-cell
        order = sorted(
            [(dist[i, j], i, j) for i, j in arena.floor_cells if np.isfinite(dist[i, j])],
            key=lambda x: x[0],
        )
        preview = [t for t in order if t[0] <= 5]
        for _, i, j in preview[::2]:
            tile = arena.floor_cells[(i, j)]
            t = float(inten[i, j])
            _set_tile_color(tile, _damage_color(max(t, 0.45)))
        self.wait(0.25)

        arena.add_updater(refresh_wave)

        wrap = Text("波沿走廊绕行 · 墙后伤害大减", font=UI_FONT, font_size=20, color=ManimColor(ACCENT_NEW_MID))
        wrap.to_corner(DR, buff=0.35)

        # Orbit while wave wraps the long path
        self.move_camera(
            theta=-55 * DEGREES + 1.05,
            phi=55 * DEGREES,
            run_time=4.2,
            rate_func=smooth,
            added_anims=[wave_r.animate.set_value(max_d * 0.55)],
        )
        self.remove(hint)
        self.add_fixed_in_frame_mobjects(wrap)
        self.play(FadeIn(wrap), run_time=0.3)

        self.move_camera(
            theta=-55 * DEGREES + 1.55,
            phi=52 * DEGREES,
            run_time=4.0,
            rate_func=smooth,
            added_anims=[wave_r.animate.set_value(max_d)],
        )

        surv_t = float(inten[SURVIVOR_IJ])
        surv_dmg = intensity_to_hp(surv_t)
        self.play(arena.survivor.animate.set_color(ManimColor(SAFE)), run_time=0.55)
        result = Text(
            f"拐角存活 · 路径 {path_len:.0f} 格 / 欧氏 {eucl:.0f} 格 · ~{surv_dmg} HP",
            font=UI_FONT,
            font_size=18,
            color=ManimColor(SAFE),
        )
        result.to_corner(DR, buff=0.35)
        self.remove(wrap)
        self.add_fixed_in_frame_mobjects(result)
        self.play(FadeIn(result, shift=UP * 0.08), run_time=0.45)

        self.wait(1.6)
        arena.remove_updater(refresh_wave)
        self.wait(0.35)
