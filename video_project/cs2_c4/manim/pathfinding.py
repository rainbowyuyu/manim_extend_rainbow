# rainbow_yu — CS2 C4 成片：搜索 / 距离场算法
"""Integrated explainer: title overview + Euclidean / BFS / Dijkstra / A* / Manhattan / Greedy.

Usage:
    python -m manim -qh video_project/cs2_c4/manim/pathfinding.py PathfindingAlgorithmsScene
"""

from __future__ import annotations

from manim import *

from video_project.cs2_c4.manim.titles import play_pathfinding_title_card
from yty_manim.basic_unit.cs2_arena import *  # noqa: F401,F403

__all__ = ("PathfindingAlgorithmsScene",)


class PathfindingAlgorithmsScene(Scene):
    """标题卡总览 → 地图逐算法展开 + 每算法精讲（整合版，无小结）。"""

    def construct(self):
        self.camera.background_color = ManimColor("#07090f")

        # ── A) 标题卡总览 ─────────────────────────────────────────────
        chrome = play_pathfinding_title_card(self, hold_tail=0.55)

        start, goal = BOMB_IJ, SURVIVOR_IJ
        specs = [
            _algo_euclidean(start),
            _algo_bfs(start, goal),
            _algo_dijkstra(start, goal),
            _algo_astar(start, goal),
            _algo_manhattan_field(start, goal),
            _algo_greedy(start, goal),
        ]

        grid_map = GridMap2D(start, goal)
        grid_map.apply_map_transform(MAP_SCALE, MAP_SHIFT)
        markers = grid_map.markers
        markers.set_z_index(Z_MARKERS)

        map_body = grid_map
        metrics_layer = VGroup()
        metrics_layer.set_z_index(Z_METRICS)
        path_group = VGroup()
        path_group.set_z_index(Z_PATH)

        panel = _place_formula_panel(_formula_panel(specs[0]).scale(0.92), map_body)

        # ── B) 无缝转场：总览淡出与地图入场同拍（禁止对 panel 先 set_opacity(0) 再 FadeIn）
        self.add(map_body, markers, metrics_layer, path_group, panel)
        map_body.set_opacity(0)
        markers.set_opacity(0)

        self.play(
            FadeOut(chrome.fade_group, shift=DOWN * 0.08),
            FadeOut(chrome.grid),
            map_body.animate.set_opacity(1),
            markers.animate.set_opacity(1),
            FadeIn(panel, shift=LEFT * 0.18),
            run_time=0.9,
            rate_func=rate_functions.ease_in_out_cubic,
        )
        self.remove(chrome.grid)
        _apply_layer_order(self, map_body, panel, metrics_layer, path_group, markers)
        self.wait(0.1)

        # ── C) 逐算法：入场 → 演示 → 精讲 → 退场 ─────────────────────
        for idx, spec in enumerate(specs):
            if idx > 0:
                new_panel = _place_formula_panel(_formula_panel(spec).scale(0.92), map_body)
                self._exit_algo(grid_map, panel, path_group, metrics_layer)
                path_group = VGroup()
                path_group.set_z_index(Z_PATH)
                self.add(path_group)
                metrics_layer = VGroup()
                metrics_layer.set_z_index(Z_METRICS)
                self.add(metrics_layer)
                grid_map.reset_tiles()
                panel = new_panel
                self.add(panel)
                self._enter_algo(panel, spec, first=False)
            else:
                self._enter_algo(panel, spec, first=True)

            badge = Text(f"{idx + 1}/{len(specs)}", font="Consolas", font_size=15, color=C_SUB)
            badge.next_to(panel[0], UP, aligned_edge=LEFT, buff=0.1)
            badge.set_z_index(Z_PANEL + 1)
            self.play(FadeIn(badge, shift=DOWN * 0.05), run_time=0.2)
            _apply_layer_order(self, map_body, panel, metrics_layer, path_group, markers)

            if spec.ring_mode:
                self._animate_ring_field(grid_map, spec)
            else:
                self._animate_layers(grid_map, spec, metrics_layer)

            if spec.path:
                path = _path_mobject(spec.path, spec.accent)
                path_group.add(path)
                self.add(path_group)
                _apply_layer_order(self, map_body, panel, metrics_layer, path_group, markers)
                self.play(Create(path), run_time=0.55, rate_func=rate_functions.ease_in_out_cubic)
                self.play(Indicate(path[1], color=WHITE, scale_factor=1.015), run_time=0.28)

            self.play(FadeOut(badge), run_time=0.15)
            # 图一完成态：停顿 0.5s 再进入精讲文字
            self.wait(0.5)
            self._play_deep_dive(spec, map_body, panel)

        self.wait(0.5)

    def _enter_algo(self, panel: VGroup, spec: AlgoSpec, *, first: bool = False) -> None:
        """算法侧栏入场。"""
        ease = rate_functions.ease_in_out_cubic
        if first:
            self.play(
                panel[0].animate.set_stroke(color=spec.accent, width=2.4),
                run_time=0.45,
                rate_func=ease,
            )
            self.play(panel[0].animate.set_stroke(color=C_PANEL_EDGE, width=1.2), run_time=0.25)
            return
        panel.shift(RIGHT * 0.4)
        self.play(
            panel.animate.shift(LEFT * 0.4),
            run_time=0.55,
            rate_func=ease,
        )
        self.play(
            panel[0].animate.set_stroke(color=spec.accent, width=2.4),
            run_time=0.3,
            rate_func=ease,
        )
        self.play(panel[0].animate.set_stroke(color=C_PANEL_EDGE, width=1.2), run_time=0.2)

    def _exit_algo(
        self,
        grid_map: GridMap2D,
        panel: VGroup,
        path_group: VGroup,
        metrics_layer: VGroup,
    ) -> None:
        """算法退场：路径/数值消散，热力回落，面板滑出。"""
        ease = rate_functions.ease_in_out_cubic
        tile_anims = [
            tile.animate.set_fill(ManimColor(C_FLOOR), opacity=1).set_stroke(
                color="#2a3a50", width=0.8, opacity=0.5
            )
            for tile in grid_map.tiles.values()
        ]
        outs = []
        if len(path_group) > 0:
            outs.append(FadeOut(path_group))
        if len(metrics_layer) > 0:
            outs.append(FadeOut(metrics_layer))
        self.play(
            *outs,
            AnimationGroup(*tile_anims, lag_ratio=0.008),
            panel.animate.shift(LEFT * 0.35).set_opacity(0),
            run_time=0.55,
            rate_func=ease,
        )
        self.remove(panel)
        if len(path_group) > 0:
            self.remove(path_group)
        if len(metrics_layer) > 0:
            self.remove(metrics_layer)
        grid_map.reset_tiles()

    def _play_deep_dive(self, spec: AlgoSpec, map_body: Mobject, panel: VGroup) -> None:
        """精讲：先出底板，文字逐段 Write；高亮只描边，避免 Indicate 吞掉文字。"""
        dive = _deep_dive_for(spec.key)
        accent = ManimColor(spec.accent)
        ease = rate_functions.ease_in_out_cubic
        pad = 0.42
        inner_w = 10.2

        dim_targets = VGroup(map_body, panel)
        self.play(dim_targets.animate.set_opacity(0.22), run_time=0.3, rate_func=ease)

        head = Text(dive.headline, font=UI_FONT, font_size=26, color=accent)
        if head.width > inner_w:
            head.set_width(inner_w)

        focus = Text(dive.formula_focus, font="Consolas", font_size=24, color=WHITE)
        if focus.width > inner_w - 0.6:
            focus.set_width(inner_w - 0.6)
        focus_bg = RoundedRectangle(
            width=min(focus.width + 0.5, inner_w),
            height=focus.height + 0.28,
            corner_radius=0.1,
            fill_color="#121a28",
            fill_opacity=1,
            stroke_color=spec.accent,
            stroke_width=1.4,
        )
        focus.move_to(focus_bg.get_center())
        focus_chip = VGroup(focus_bg, focus)

        step_rows = VGroup()
        step_parts: list[tuple[Text, Text, Text]] = []
        for i, (title, body) in enumerate(dive.steps):
            num = Text(f"{i + 1:02d}", font="Consolas", font_size=17, color=accent)
            t = Text(title, font=UI_FONT, font_size=18, color=ManimColor(C_TITLE))
            b = Text(body, font=UI_FONT, font_size=14, color=C_SUB)
            text_col = VGroup(t, b).arrange(DOWN, buff=0.06, aligned_edge=LEFT)
            max_body = inner_w - 0.7
            if text_col.width > max_body:
                text_col.set_width(max_body)
            row = VGroup(num, text_col).arrange(RIGHT, buff=0.2, aligned_edge=UP)
            step_rows.add(row)
            step_parts.append((num, t, b))
        step_rows.arrange(DOWN, buff=0.2, aligned_edge=LEFT)

        insight_txt = Text(dive.insight, font=UI_FONT, font_size=15, color=ManimColor(C_TITLE))
        if insight_txt.width > inner_w - 0.5:
            insight_txt.set_width(inner_w - 0.5)
        insight_bar = RoundedRectangle(
            width=inner_w,
            height=insight_txt.height + 0.36,
            corner_radius=0.1,
            fill_color=interpolate_color(ManimColor("#121a28"), accent, 0.18),
            fill_opacity=1,
            stroke_color=spec.accent,
            stroke_width=0,
        )
        insight_txt.move_to(insight_bar.get_center())
        insight = VGroup(insight_bar, insight_txt)

        content = VGroup(head, focus_chip, step_rows, insight).arrange(
            DOWN, buff=0.26, aligned_edge=LEFT
        )

        board = RoundedRectangle(
            width=content.width + 2 * pad,
            height=content.height + 2 * pad,
            corner_radius=0.16,
            fill_color="#0a101a",
            fill_opacity=0.97,
            stroke_color=spec.accent,
            stroke_width=2.0,
        )
        content.move_to(board.get_center())
        layer = VGroup(board, content)
        layer.move_to(ORIGIN + DOWN * 0.25)
        if layer.get_top()[1] > 3.2:
            layer.shift(DOWN * (layer.get_top()[1] - 3.2))
        if layer.get_bottom()[1] < -3.5:
            layer.scale_to_fit_height(6.5)
            layer.move_to(ORIGIN + DOWN * 0.2)
        layer.set_z_index(20)

        # 先只显示底板；文字稍后 Write 进场（避免 opacity=0 + Write 无效）
        self.remove(*[m for m in (head, focus_chip, step_rows, insight) if m in self.mobjects])
        self.add(board)
        board.set_z_index(20)
        for m in (head, focus_bg, focus, insight_bar, insight_txt):
            m.set_z_index(21)
        for num, t, b in step_parts:
            num.set_z_index(21)
            t.set_z_index(21)
            b.set_z_index(21)

        board.shift(DOWN * 0.2)
        board.set_opacity(0)
        self.play(board.animate.shift(UP * 0.2).set_opacity(1), run_time=0.45, rate_func=ease)
        self.wait(0.15)

        # 图二：文字逐段 Write
        self.play(Write(head), run_time=0.55, rate_func=ease)
        self.wait(0.12)

        self.play(FadeIn(focus_bg, scale=0.96), run_time=0.25)
        self.play(Write(focus), run_time=0.55, rate_func=ease)
        self.wait(0.15)

        for num, t, b in step_parts:
            self.play(Write(num), run_time=0.28, rate_func=ease)
            self.play(Write(t), run_time=0.4, rate_func=ease)
            self.play(Write(b), run_time=0.55, rate_func=ease)
            self.wait(0.2)

        self.play(FadeIn(insight_bar), run_time=0.3)
        self.play(Write(insight_txt), run_time=0.75, rate_func=ease)
        self.wait(0.2)

        # 图三高亮：只加描边脉冲，绝不 Indicate 整组（会把文字染成底色导致「消失」）
        self.bring_to_front(insight_txt)
        self.play(
            insight_bar.animate.set_stroke(color=accent, width=2.8, opacity=1),
            run_time=0.4,
            rate_func=ease,
        )
        self.play(
            insight_bar.animate.set_stroke(width=0, opacity=0),
            run_time=0.35,
            rate_func=ease,
        )
        self.wait(0.7)

        outro = VGroup(board, head, focus_bg, focus, step_rows, insight_bar, insight_txt)
        self.play(FadeOut(outro, shift=DOWN * 0.15), run_time=0.4, rate_func=ease)
        self.play(dim_targets.animate.set_opacity(1), run_time=0.28, rate_func=ease)
        self.remove(board, head, focus_bg, focus, step_rows, insight_bar, insight_txt)

    def _animate_layers(self, grid_map: GridMap2D, spec: AlgoSpec, metrics_layer: VGroup) -> None:
        finite = spec.dist[np.isfinite(spec.dist)]
        max_d = float(finite.max()) if finite.size else 1.0
        show_metrics = spec.key in ("astar", "greedy", "dijkstra")
        placed: set[tuple[int, int]] = set()
        ease = rate_functions.ease_in_out_cubic

        for layer in spec.layers:
            tile_anims = []
            label_anims = []
            for i, j in layer:
                t = float(np.clip(1.0 - spec.dist[i, j] / max_d, 0, 1)) if max_d > 0 else 0.5
                col = _heat_color(0.25 + 0.75 * (1.0 - t))
                tile = grid_map.tiles[(i, j)]
                tile_anims.append(
                    tile.animate.set_fill(col, opacity=1).set_stroke(color=col, width=0.6, opacity=0.35)
                )
                if show_metrics and (i, j) in spec.cell_metrics and (i, j) not in placed:
                    lbl = grid_map.make_metric_label((i, j), spec.cell_metrics[(i, j)])
                    if lbl is not None:
                        placed.add((i, j))
                        metrics_layer.add(lbl)
                        label_anims.append(FadeIn(lbl, scale=0.9))
            if tile_anims:
                self.play(
                    LaggedStart(*tile_anims, lag_ratio=0.045),
                    *([LaggedStart(*label_anims, lag_ratio=0.08)] if label_anims else []),
                    run_time=0.26,
                    rate_func=ease,
                )

    def _animate_ring_field(self, grid_map: GridMap2D, spec: AlgoSpec) -> None:
        prog = ValueTracker(0.0)
        finite = spec.dist[np.isfinite(spec.dist)]
        max_d = float(finite.max()) if finite.size else 1.0

        def _ring_updater(_mob) -> None:
            r = prog.get_value()
            for i, j in grid_map.tiles:
                d = spec.dist[i, j]
                if not np.isfinite(d) or d > r:
                    grid_map.tiles[(i, j)].set_fill(ManimColor(C_FLOOR), opacity=1)
                    continue
                t = float(np.clip(1.0 - d / max_d, 0, 1))
                col = _heat_color(0.2 + 0.8 * (1.0 - t))
                if spec.key == "euclid":
                    col = interpolate_color(ManimColor(C_EUCL), ManimColor(C_VIS_HOT), t)
                grid_map.tiles[(i, j)].set_fill(col, opacity=1)

        grid_map.add_updater(_ring_updater)
        self.play(
            prog.animate.set_value(spec.max_ring),
            run_time=2.35,
            rate_func=rate_functions.ease_in_out_cubic,
        )
        grid_map.remove_updater(_ring_updater)
        self.wait(0.06)
