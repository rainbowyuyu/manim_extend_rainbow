# rainbow_yu — CS2 C4 成片：三维爆炸伤害场
"""C4 风格伤害丘：中心致死圈 + 外圈衰减；红→绿蓝高度渐变；弯曲下滑轨迹。

Usage:
    python -m manim -qh --disable_caching \
        video_project/cs2_c4/manim/damage_field_3d.py ExplosionDamageField3D
"""

from __future__ import annotations

from manim import *

from yty_manim.basic_unit.cs2_damage import *  # noqa: F401,F403

__all__ = ("ExplosionDamageField3D",)


class ExplosionDamageField3D(ThreeDScene):
    """大红爆炸区 + 红→绿蓝渐变曲面 + 弯曲下滑轨迹。"""

    def construct(self):
        self.camera.background_color = ManimColor(C_BG)
        # 稍远一点，容纳更大平面
        self.set_camera_orientation(phi=52 * DEGREES, theta=-26 * DEGREES, zoom=0.58)

        surface = Surface(
            lambda u, v: np.array([u, v, _height(u, v)]),
            u_range=[X_MIN, X_MAX],
            v_range=[Y_MIN, Y_MAX],
            resolution=(40, 34),
            fill_opacity=0.95,
            stroke_width=0.15,
            stroke_opacity=0.08,
        )
        _color_surface_by_height(surface)

        # 致死圈：默认在 XY 平面，只需抬到平台高度（不要再 rotate 成竖直）
        lethal_z = _height(0.0, 0.0) - 0.02
        lethal_ring = Circle(
            radius=R_LETHAL,
            color=C_LETHAL,
            stroke_width=3.0,
            stroke_opacity=0.9,
        )
        lethal_ring.move_to([0.0, 0.0, lethal_z])

        core = Sphere(radius=0.11, resolution=(8, 8))
        core.set_color(ManimColor(C_CORE)).move_to([0.0, 0.0, _height(0.0, 0.0) + 0.07])

        traj = _curved_descent_path()
        path = VMobject()
        path.set_points_smoothly([np.array(p) for p in traj])
        path.set_stroke(color=C_TRAIL, width=4.4, opacity=0.95)
        glow = path.copy().set_stroke(color="#fde047", width=10.5, opacity=0.28)

        probe = Sphere(radius=0.13, resolution=(10, 10))
        probe.set_color(ManimColor(C_DOT)).move_to(traj[0])
        # 跟随球的小环也水平贴地法向（XY）
        ring = Circle(radius=0.22, color="#a5f3fc", stroke_width=2.6)
        ring.move_to(traj[0])

        surface.save_state()
        surface.stretch(0.02, 2, about_point=ORIGIN)
        self.play(
            Restore(surface),
            FadeIn(core, scale=0.5),
            FadeIn(lethal_ring),
            run_time=1.35,
            rate_func=rate_functions.ease_out_cubic,
        )
        self.wait(0.3)

        self.play(FadeIn(probe, scale=0.6), FadeIn(ring), run_time=0.4)
        ring.add_updater(lambda m: m.move_to(probe.get_center()))

        self.play(
            Create(glow),
            Create(path),
            MoveAlongPath(probe, path.copy()),
            run_time=8.8,
            rate_func=rate_functions.ease_in_out_sine,
        )
        ring.clear_updaters()
        ring.move_to(probe.get_center())

        self.play(
            ring.animate.scale(2.2).set_stroke(opacity=0),
            Flash(probe, color="#ffffff", line_length=0.2, num_lines=10, flash_radius=0.35),
            run_time=0.7,
            rate_func=rate_functions.ease_out_cubic,
        )
        self.wait(0.9)
