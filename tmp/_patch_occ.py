from pathlib import Path

p = Path(r"d:\python_project\manim_extend_rainbow\yty_manim\application\explosion_prebake_viz.py")
t = p.read_text(encoding="utf-8")
start = t.index("    # ── 6 遮挡")
end = t.index("    # ── 7 遮挡烘焙对比")
new = r'''    # ── 6 遮挡 ────────────────────────────────────────────────────────
    def add_occlusion(self):
        self.remove(self.radial_grid)
        self.play(FadeOut(self.bake_title), FadeOut(self.bake_arr), run_time=_w(0.35))

        self.frame = map_frame()
        self.src = ExplosionSource(self.e, RADIUS)
        self.wall_mobs = VGroup(*[w.as_rect() for w in self.walls])
        self.player_a = PlayerMarker(self.pa, "A", C_PLAYER_A)
        self.player_b = PlayerMarker(self.pb, "B", C_PLAYER_B)
        self.player_c = PlayerMarker(self.pc, "C", C_PLAYER_C)
        self.play(
            FadeIn(self.frame), FadeIn(self.wall_mobs), FadeIn(self.src),
            FadeIn(self.player_a), FadeIn(self.player_b), FadeIn(self.player_c),
            run_time=_w(0.6),
        )
        title = Text("只有距离还不够：墙体与材质", font=UI_FONT, font_size=24, color=C_TITLE).to_edge(UP, buff=0.3)
        self.play(FadeIn(title), run_time=_w(0.4))

        va = visibility_factor(self.e, self.pa, self.walls)
        vb = visibility_factor(self.e, self.pb, self.walls)
        vc = visibility_factor(self.e, self.pc, self.walls)
        wall0 = self.walls[0]
        stop = np.array([wall0.x1, float(self.pc[1]), 0.0])
        ra = Line(self.e, self.pa, stroke_color=C_PLAYER_A, stroke_width=2.5)
        rb = Line(self.e, self.pb, stroke_color=C_PLAYER_B, stroke_width=2.5)
        rc = Line(self.e, stop, stroke_color=C_PLAYER_C, stroke_width=2.5)
        flash = Dot(stop, radius=0.07, color=C_WARN)

        self.play(Create(ra), run_time=_w(0.5))
        ta = fm(f"V_A={va:.2f}", font_size=26, color=C_PLAYER_A).next_to(self.player_a, RIGHT)
        self.play(FadeIn(ta), run_time=_w(0.3))
        self.play(Create(rb), run_time=_w(0.5))
        tb = fm(f"V_B={vb:.2f}", font_size=26, color=C_PLAYER_B).next_to(self.player_b, DOWN)
        self.play(FadeIn(tb), rb.animate.set_stroke(opacity=0.45), run_time=_w(0.4))
        self.play(Create(rc), FadeIn(flash), run_time=_w(0.55))
        tc = fm(f"V_C={vc:.2f}", font_size=26, color=C_PLAYER_C).next_to(self.player_c, LEFT)
        self.play(FadeIn(tc), run_time=_w(0.3))

        table = FormulaPanel(
            ["开放 1.00", "薄木板 0.45", "砖墙 0.15", "厚混凝土 0.00"],
            title="材质透过（演示）",
            width=3.6,
        ).to_edge(RIGHT, buff=0.3)
        self.play(FadeIn(table), run_time=_w(0.5))
        formula = fm("D = D_max*(1-u)^2 * V(e,p)", font_size=26, color=C_TITLE).next_to(title, DOWN, buff=0.2)
        self.play(FadeIn(formula), run_time=_w(0.5))

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
            self.play(FadeIn(ring), FadeIn(num), run_time=_w(0.3))
        punch = Text("距离近，不代表伤害一定高", font=UI_FONT, font_size=26, color=C_WARN)
        punch.to_edge(DOWN, buff=0.35)
        self.play(FadeIn(punch), run_time=_w(0.5))
        self.wait(_w(2.0))
        clear = [
            ra, rb, rc, flash, ta, tb, tc, table, formula, title, punch, dmg_labels,
            self.player_a, self.player_b, self.player_c, self.frame, self.src, self.wall_mobs,
        ]
        self.play(*[FadeOut(m) for m in clear], run_time=_w(0.5))

'''
p.write_text(t[:start] + new + t[end:], encoding="utf-8")
print("ok")
