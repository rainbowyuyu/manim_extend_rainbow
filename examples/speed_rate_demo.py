# rainbow_yu examples — speed_rate_fuc demos
"""为 disposition.speed_rate_fuc 中每条 rate_func 生成示例动画。"""

from __future__ import annotations

from manim import *

from yty_manim.disposition.speed_rate_fuc import rate_presets

# 去再回类终点不为 1；轨迹类用水平位移展示进度
_OSCILLATING = {"there_and_back", "there_and_back_with_pause", "wiggle"}


def _sample_bounds(rf, n: int = 200) -> tuple[float, float]:
    ys = [float(rf(i / n)) for i in range(n + 1)]
    lo, hi = min(ys), max(ys)
    pad = 0.12 * max(hi - lo, 1.0)
    return lo - pad, hi + pad


class RateFuncDemo(Scene):
    """单条缓动演示：曲线 + 水平滑块。子类设置 rate_name。"""

    rate_name: str = "linear"
    run_seconds: float = 1.35

    def construct(self):
        name = self.rate_name
        rf = rate_presets[name]
        y_min, y_max = _sample_bounds(rf)

        title = Text(name, font="Sans", font_size=30, color="#e8eef8")
        title.to_edge(UP, buff=0.28)

        ax = Axes(
            x_range=[0, 1, 0.25],
            y_range=[y_min, y_max, 0.25],
            x_length=6.4,
            y_length=3.2,
            axis_config={"color": GREY_B, "stroke_width": 1.5, "include_tip": False},
            tips=False,
        )
        ax.shift(UP * 0.15)

        x_lab = Text("t", font="Sans", font_size=18, color=GREY_A).next_to(ax.x_axis, RIGHT, buff=0.12)
        y_lab = Text("f(t)", font="Sans", font_size=18, color=GREY_A).next_to(ax.y_axis, UP, buff=0.12)

        curve = ax.plot(lambda t: float(rf(t)), x_range=[0, 1], color="#3de0c8", stroke_width=4)

        track_y = -3.15
        track = Line(LEFT * 3.2, RIGHT * 3.2, color=GREY_BROWN, stroke_width=3).move_to([0, track_y, 0])
        start_dot = Dot(track.get_start(), radius=0.06, color=GREY_B)
        end_mark = Dot(track.get_end(), radius=0.05, color=GREY_B)
        ball = Dot(track.get_start(), radius=0.14, color="#ff6b4a")

        hint = Text(
            "progress →",
            font="Sans",
            font_size=16,
            color=GREY_B,
        ).next_to(track, DOWN, buff=0.18)

        self.add(title, ax, x_lab, y_lab, curve, track, start_dot, end_mark, ball, hint)

        tracer = Dot(color="#f7c548", radius=0.08)
        tracer.move_to(ax.c2p(0, float(rf(0))))
        self.add(tracer)

        t_tracker = ValueTracker(0.0)

        def sync_mobs(_=None):
            t = t_tracker.get_value()
            y = float(rf(t))
            tracer.move_to(ax.c2p(t, y))
            # 水平位移：普通曲线用 [0,1]；振荡类映射到轨道中点对称
            if name in _OSCILLATING:
                # f 可能在 [-1,1] 或 [0,1] 往返：用 y 相对 [y_min,y_max] 映射到轨道
                u = (y - y_min) / max(y_max - y_min, 1e-9)
            else:
                u = float(np.clip(y, 0.0, 1.0)) if y_max <= 1.35 and y_min >= -0.35 else (y - y_min) / max(
                    y_max - y_min, 1e-9
                )
            ball.move_to(track.point_from_proportion(float(np.clip(u, 0.0, 1.0))))

        ball.add_updater(sync_mobs)
        tracer.add_updater(sync_mobs)
        sync_mobs()

        self.play(
            t_tracker.animate.set_value(1.0),
            run_time=self.run_seconds,
            rate_func=linear,
        )
        ball.clear_updaters()
        tracer.clear_updaters()
        self.wait(0.25)


def _register_scenes() -> None:
    for name in rate_presets:
        cls_name = f"Rate_{name}"
        globals()[cls_name] = type(cls_name, (RateFuncDemo,), {"rate_name": name})


_register_scenes()
