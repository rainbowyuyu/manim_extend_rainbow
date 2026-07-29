# rainbow_yu🐋✨  
Improvements and additions to animation control and operations based on Manim.  
For basic Manim knowledge, please refer to [manim](https://github.com/manimCommunity/manim)

[![language](https://img.shields.io/badge/language-English-blue)](README.md) [![language](https://img.shields.io/badge/language-中文-blue)](README-ch.md)
---

### Installation Instructions:  
1. **Configure the LaTeX environment first**  
- For detailed instructions, refer to [texlive](https://tug.org/texlive/)  
> [!Warning]  
> **WARNING:** Be sure to configure the LaTeX environment variables properly.  

2. **Install dependencies**  
- Developed with `Python 3.10`, the minimum required version is `Python 3.8`.  
```bash
git clone https://github.com/rainbowyuyu/manim_extend_rainbow.git
cd ./manim_extend_rainbow
pip install -r requirements.txt
```

---

### File Structure:  
yty_manim  
├── [examples.ipynb](examples/examples.ipynb)  
├── [disposition](yty_manim%2Fdisposition)  
│ ├── [speed_rate_fuc.py](yty_manim%2Fdisposition%2Fspeed_rate_fuc.py)  
│ ├── [speed_rate_fuc.md](yty_manim%2Fdisposition%2Fspeed_rate_fuc.md)  
│ └── [fonts_and_colors.py](yty_manim%2Fdisposition%2Ffonts_and_colors.py)  
├── [basic_unit](yty_manim%2Fbasic_unit)  
│ ├── [squ_tex.py](yty_manim%2Fbasic_unit%2Fsqu_tex.py)  
│ ├── [dec_bin.py](yty_manim%2Fbasic_unit%2Fdec_bin.py)  
│ ├── [screen_cycle.py](yty_manim%2Fbasic_unit%2Fscreen_cycle.py)  
│ ├── [threed_vgp.py](yty_manim%2Fbasic_unit%2Fthreed_vgp.py)  
│ ├── [code_step.py](yty_manim%2Fbasic_unit%2Fcode_step.py)  
│ ├── [shapes.py](yty_manim%2Fbasic_unit%2Fshapes.py)  
│ ├── [cs2_arena.py](yty_manim%2Fbasic_unit%2Fcs2_arena.py)  
│ ├── [cs2_damage.py](yty_manim%2Fbasic_unit%2Fcs2_damage.py)  
│ └── [cs2_map.py](yty_manim%2Fbasic_unit%2Fcs2_map.py)  
├── [application](yty_manim%2Fapplication)  
│ ├── [matrix_yty.py](yty_manim%2Fapplication%2Fmatrix_yty.py)  
│ ├── [page_replacement.py](yty_manim%2Fapplication%2Fpage_replacement.py)  
│ ├── [title_animate.py](yty_manim%2Fapplication%2Ftitle_animate.py)  
│ └── [s.py](yty_manim%2Fapplication%2Fs.py)  
└── [tools](yty_manim%2Ftools)  
  └── [map_editor](yty_manim%2Ftools%2Fmap_editor)  

video_project  
└── [cs2_c4](video_project%2Fcs2_c4)  
  ├── [manim](video_project%2Fcs2_c4%2Fmanim)  
  ├── [cs2_c4_data](video_project%2Fcs2_c4%2Fcs2_c4_data)  
  ├── [cs2_c4_edit](video_project%2Fcs2_c4%2Fcs2_c4_edit)  
  └── [cs2_c4_footage](video_project%2Fcs2_c4%2Fcs2_c4_footage)  

---

## disposition

---

### speed_rate_fuc.py

Collection of Manim `rate_func` easing curves (polynomial / sine·expo·circ / back·elastic·bounce / there-and-back, etc.).

Full guide, usage tips, and a GIF demo for each curve:  
→ **[speed_rate_fuc.md](yty_manim/disposition/speed_rate_fuc.md)**

```python
from yty_manim.disposition.speed_rate_fuc import ease_in_out_cubic, rate_presets

self.play(mob.animate.shift(RIGHT), rate_func=ease_in_out_cubic)
self.play(..., rate_func=rate_presets["ease_out_back"])
```

Regenerate demo GIFs:

```bash
python examples/render_speed_rate_gifs.py
```

### fonts_and_colors.py

Font list, gradient palettes, `typedict` shape styles, and CS2-related defaults (`cs2_arena_3d` / `cs2_damage` / `cs2_mirage_map`, etc.).

---

## basic_unit

---

### squ_tex.py
Contains classes `SquTex`, `SquTexSlide`, and `Stack`

![squ_tex](yty_manim/examples/squ_tex.png)

---

#### SquTex

A data block, inheriting from :class:`~.VGroup`,  
- Commonly used for demonstrations of data structures and binary encoding,  
- Combines squares and numbers together, supporting unified and individual animations,  
- The `distance` member records the gap between data when first constructed,  
- Single animations can be created using :method:`animate_one_by_one` to group animations,  
- When creating the data block, all modifiable parameters are passed to the :class:`~.Square` class,  
- To modify other parameters, use :method:`change_square` and :method:`change_text`,  
- Be cautious when using :method:`change_text`, as it will change the hierarchy of the original object,  
- Use :method:`add_bracket` to add brackets to all negative numbers in the data block.

Usage example:

```python
from manim import *
from yty_manim.basic_unit.squ_tex import SquTex

class SquTexCreate(Scene):
    def construct(self):
        t = SquTex("rainbow")
        self.play(t.animate_one_by_one(FadeIn , scale=1.5))
        self.wait()
```

---

#### SquTexSlide

A sliding data block, inheriting from :class:`~.SquTex`,  
- Adds sliding animation to the data block,  
- Use :method:`slide` for basic positional sliding,  
- Use :method:`slide_fade` for internal or external sliding with smooth fade-in and fade-out for the data block.

Usage example:

```python
from manim import *
from yty_manim.basic_unit.squ_tex import SquTexSlide

class SquTexSlideBasic(Scene):
    def construct(self):
        s = SquTexSlide("rainbow")
        self.add(s)
        self.wait()
        for i in range(len(s)):
            self.play(*s.slide(-1))
        self.wait()
```

---

#### Stack

A stack-oriented data block, inheriting from :class:`~.SquTexSlide`,  
- Adds structure transforms on top of sliding blocks: swap, reverse, and a following pointer,  
- Use :method:`move_pointer` to move the pointer to an index,  
- Use :method:`swap` / :method:`reverse` (unpack the returned animation group in `play`),  
- :method:`pop` / :method:`push` are extended to keep the pointer in sync.

Usage example:

```python
from manim import *
from yty_manim.basic_unit.squ_tex import Stack
from yty_manim.disposition.fonts_and_colors import gradient_dict, typedict

class StackClass(Scene):
    def construct(self):
        lst = [1, 2, 3, 4, 5]
        s = Stack(lst, pointer_direction=UP, need_pointer=True, **typedict["default_st_type"])
        for i in range(len(lst)):
            s[i].set_color(gradient_dict["rainbow_color"][i % 7])
        self.play(Create(s))
        self.play(s.animate.move_pointer(2))
        self.play(*s.swap(0, 3))
        self.play(*s.reverse())
        self.wait()
```

---

### dec_bin.py
Contains classes `BinNumber` and `Bin4SquTex`  
- `BinNumber` handles binary numeric logic; `Bin4SquTex` is planned to connect binary display to `SquTex` animations (still being improved).

---

#### BinNumber

A data block for binary numbers,  
- Records the sign bit, integer part, and fractional part of a binary number,  
- Converts decimal numbers to an ideal binary format,  
- Can perform operations on binary numbers.

- Initialize with empty values for the object, then use :method:`bin2dec` to convert the binary object to a decimal number,  
- Use :method:`standardize` to standardize the binary number format,  
- Use :method:`ex_one` to convert to its one's complement,  
- Use :method:`ex_two` to convert to its two's complement,  
- Use :method:`information` to display all parameter information,  
- Use :method:`cal_check` to check if precision will be exceeded during calculations,  
- Operator overloading methods follow the format of the first operand.

Usage example:

```python
from yty_manim.basic_unit.dec_bin import BinNumber

# Define decimal number and convert it to binary
test_bin = BinNumber(-0.2, 8, 1, True)
print(test_bin)
print(test_bin.ex_one())
print(test_bin.ex_two())
```

---

### screen_cycle.py
Contains classes `ScreenCycle` and `Directory`

---

#### ScreenCycle

A title-screen carousel, inheriting from :class:`~.VGroup`,  
- Commonly used for intro title rotation and parking the active title in a corner,  
- Construct with a list of title strings; optionally set font, gradient, spacing, and magnification,  
- Use :method:`step_forward` to advance (highlight current, fade others),  
- Use :method:`set_to_edge` / :method:`set_back` to move the title to a corner or restore the carousel.

Usage example:

```python
from manim import *
from yty_manim.basic_unit.screen_cycle import ScreenCycle

class ScreenTest(Scene):
    def construct(self):
        text_list = [
            "Hello World",
            "Hell Worl",
            "Hel Wor",
            "He Wo",
        ]
        s = ScreenCycle(text_list)
        self.add(s)
        for i in range(len(text_list)):
            self.play(s.animate.step_forward())
        self.play(s.animate.set_to_edge(UL))
        self.play(s.animate.set_back())
```

---

#### Directory

A table-of-contents visual, inheriting from :class:`~.VGroup`,  
- Left-side dotted timeline plus chapter titles on the right,  
- Use :method:`step_forward` to light up the next item in sync with narration.

Usage example:

```python
from manim import *
from yty_manim.basic_unit.screen_cycle import Directory
from yty_manim.disposition.fonts_and_colors import text_font

class DirectoryPage(Scene):
    def construct(self):
        title = [
            "Pages & replacement",
            "Thrashing & Belady",
            "Replacement algorithms",
            "Stack structure",
            "Code walkthrough",
        ]
        d = Directory(title, font=text_font[0])
        d[1].set_color(GRAY)
        self.play(Write(d[0:2]), run_time=2)
        for i in range(len(title)):
            d.step_forward(self)
```

---

### threed_vgp.py
Contains class `ThreeDVgp`

---

#### ThreeDVgp

A layered 3D object group, inheriting from :class:`~.VGroup`,  
- Copies any 2D mobject along `OUT` to create extruded thickness,  
- Use :method:`set_depth_gradient_color` for a depth color ramp,  
- Use :method:`set_depth_gradient_opacity` for a depth opacity ramp,  
- Use :method:`animate_together` to apply the same animation to every layer,  
- Use :method:`set_shade` to offset a bottom shadow layer.

Usage example:

```python
from manim import *
from yty_manim.basic_unit.threed_vgp import ThreeDVgp
from yty_manim.disposition.fonts_and_colors import color_dict

class PictureShow(ThreeDScene):
    def construct(self):
        self.camera.background_color = color_dict["bg"]
        t2d = Text("rainbow")
        t3d = ThreeDVgp(t2d, layer_depth=20)
        self.set_camera_orientation(0.25 * PI, -0.25 * PI, 0.25 * PI)
        t3d.set_depth_gradient_opacity([0, 1])
        t3d.set_depth_gradient_color(WHITE, BLUE_D)
        self.add(t3d)
```

---

### code_step.py
Contains class `CodeStep`

---

#### CodeStep

Stepwise code writing, inheriting from :class:`~.Code`,  
- Tracks how many lines have already been revealed,  
- Use :method:`write_code` to write the next `lines`; with `is_auto_runtime=True`, duration scales with character count,  
- Useful when walking through pseudocode in sync with narration.

Usage example:

```python
from manim import *
from yty_manim.basic_unit.code_step import CodeStep

class CodeShow(Scene):
    def construct(self):
        c1 = CodeStep(
            code_string="a = 1\nb = 2\nprint(a + b)",
            language="python",
        )
        self.add(c1)
        for i in range(len(c1[2])):
            c1.write_code(self, 1, is_auto_runtime=True)
            self.wait(0.3)
```

---

### shapes.py
Contains class `Book`

---

#### Book

A book-shaped decoration, inheriting from :class:`~.VGroup`,  
- Built from a cover rectangle, side thickness, top cut, and vertical title,  
- `index` sets `z_index` for stacking order,  
- `fill_color` / `stroke_color` control the cover fill and stroke,  
- Handy for intros, shelves, and chapter decorations.

Usage example:

```python
from manim import *
from yty_manim.basic_unit.shapes import Book

class BookShape(Scene):
    def construct(self):
        b1 = Book("...", 0, BLUE, BLUE_E)
        b2 = Book("CV", 1, GREEN, GREEN_E)
        self.add(b1.shift(LEFT * 0.5), b2)
        self.wait()
```

---

### cs2_arena.py
Contains `Arena3D`, `GridMap2D`, `AlgoSpec`, and shared toy-map constants `GRID`, `BOMB_IJ`, `SURVIVOR_IJ`  
- The 3D arena and 2D pathfinding grid share the same topology for sphere-blast vs path-wave comparisons.

---

#### Arena3D

A CS2 C4–style 3D arena, inheriting from :class:`~.VGroup`,  
- Builds floor plates, merged walls, bomb and survivor markers from `GRID`,  
- Often paired with shockwave / sphere-blast `ThreeDScene`s,  
- Helpers such as `_bfs_dist` / `_bfs_path` and damage coloring live in the same module.

Usage example:

```python
from manim import *
from yty_manim.basic_unit.cs2_arena import Arena3D

class ArenaShow(ThreeDScene):
    def construct(self):
        self.set_camera_orientation(phi=58 * DEGREES, theta=-55 * DEGREES, zoom=0.72)
        arena = Arena3D()
        self.play(FadeIn(arena), run_time=1.2)
        self.wait()
```

---

#### GridMap2D

A 2D grid map for pathfinding visuals, inheriting from :class:`~.VGroup`,  
- Shares `GRID` / `BOMB_IJ` / `SURVIVOR_IJ` with `Arena3D`,  
- Supports layered coloring, path polylines, and endpoint markers,  
- Use :method:`apply_map_transform` to scale/shift for side-panel layouts.

Usage example:

```python
from manim import *
from yty_manim.basic_unit.cs2_arena import (
    BOMB_IJ,
    SURVIVOR_IJ,
    MAP_SCALE,
    MAP_SHIFT,
    GridMap2D,
)

class GridShow(Scene):
    def construct(self):
        m = GridMap2D(BOMB_IJ, SURVIVOR_IJ)
        m.apply_map_transform(MAP_SCALE, MAP_SHIFT)
        self.add(m, m.markers)
        self.wait()
```

---

### cs2_damage.py
Contains `ExplosionMarker`, `PlayerMarker`, `DamageGrid`, `HealthBar`, `DamageHill3D`,  
plus helpers such as `bake_damage_field` / `bilinear_sample` / `make_demo_walls`  
- Used to explain distance falloff × occlusion → grid bake → runtime sample → HP preview.

---

#### ExplosionMarker

A teaching explosion marker, inheriting from :class:`~.VGroup`,  
- Draws a core, glow, and radius ring (visual only),  
- Different from the `ExplosionSource` data class in `tools.map_editor`; alias `ExplosionSource = ExplosionMarker` is kept here.

Usage example:

```python
from manim import *
from yty_manim.basic_unit.cs2_damage import ExplosionMarker, RADIUS

class MarkerShow(Scene):
    def construct(self):
        src = ExplosionMarker(ORIGIN, RADIUS)
        self.play(FadeIn(src))
        self.wait()
```

---

#### DamageGrid

A prebaked damage heat grid, inheriting from :class:`~.Group` (avoids empty-anchor zip issues),  
- Takes a world-point lattice and a damage field, then colors each sample by intensity,  
- Works with :func:`make_grid_points` / :func:`bake_damage_field` / :func:`bilinear_sample`.

Usage example:

```python
from manim import *
import numpy as np
from yty_manim.basic_unit.cs2_damage import (
    D_MAX,
    DamageGrid,
    ExplosionMarker,
    RADIUS,
    bake_damage_field,
    make_demo_walls,
    make_grid_points,
)

class DamageGridShow(Scene):
    def construct(self):
        walls = make_demo_walls()
        pts, *_ = make_grid_points()
        e = np.array([-2.2, 0.6, 0.0])
        field = bake_damage_field(pts, e, RADIUS, D_MAX, walls)
        grid = DamageGrid(pts, field)
        self.add(grid, ExplosionMarker(e, RADIUS))
        self.wait()
```

---

#### DamageHill3D

A 3D damage-hill helper (teaching model, not an engine port),  
- :method:`height` returns surface height; :method:`color_surface` colors faces by height,  
- :method:`curved_descent_path` returns a ground-following Bézier sample path,  
- Full production scene: `video_project/cs2_c4/manim/damage_field_3d.py`.

Usage example:

```python
from manim import *
from yty_manim.basic_unit.cs2_damage import DamageHill3D, X_MIN, X_MAX, Y_MIN, Y_MAX

class HillShow(ThreeDScene):
    def construct(self):
        hill = DamageHill3D()
        surface = Surface(
            lambda u, v: np.array([u, v, hill.height(u, v)]),
            u_range=[X_MIN, X_MAX],
            v_range=[Y_MIN, Y_MAX],
            resolution=(24, 20),
        )
        hill.color_surface(surface)
        self.set_camera_orientation(phi=70 * DEGREES, theta=-40 * DEGREES)
        self.add(surface)
        self.wait()
```

---

### cs2_map.py
Contains `MirageVectorMap`, `GridMapView`, `MirageOverview`, plus Mirage walkability, site constants, and engine snippets  
- Data: `WALKABLE`, `WAVE_SPEED_M_S`, `dijkstra_wave_field`, `arrival_time_seconds`  
- Rendering: vector heat map, MapBundle view, shockwave tracker binding

---

#### MirageVectorMap

A Mirage top-down vector map with a fluid shockwave front, inheriting from :class:`~.VGroup`,  
- Draws floor and heat layers from the 128×96 walkable grid,  
- Use :func:`bind_fluid_wave_tracker` to sync a `ValueTracker` radius to the contour front.

Usage example:

```python
from manim import *
import numpy as np
from yty_manim.basic_unit.cs2_map import (
    BOMB_SITE_A,
    MirageVectorMap,
    bind_fluid_wave_tracker,
    dijkstra_wave_field,
)

class MirageMapShow(Scene):
    def construct(self):
        dist, _ = dijkstra_wave_field(BOMB_SITE_A.norm)
        m = MirageVectorMap(dist=dist)
        r = ValueTracker(0.0)
        bind_fluid_wave_tracker(m, r)
        self.add(m)
        self.play(r.animate.set_value(float(np.nanmax(dist[np.isfinite(dist)]))), run_time=4)
        self.wait()
```

---

#### GridMapView

A generic MapBundle grid view, inheriting from :class:`~.VGroup`,  
- Loads a bundle from `tools.map_editor` and draws walkable cells plus shockwave heat,  
- Assemble with :func:`build_map_view_from_bundle` / :func:`bind_wave_tracker`.

Usage example:

```python
from manim import *
from yty_manim.basic_unit.cs2_map import bind_wave_tracker, build_map_view_from_bundle
from yty_manim.tools.map_editor.map_bundle import MapBundle, default_maps_dir

class BundleMapShow(Scene):
    def construct(self):
        bundle = MapBundle.load(default_maps_dir() / "your_map")
        view = build_map_view_from_bundle(bundle)
        r = ValueTracker(0.0)
        bind_wave_tracker(view, r)
        self.add(view)
        self.play(r.animate.set_value(40), run_time=3)
```

---

## application

---

### matrix_yty.py
Contains base class `MatrixCal` and computation classes `MatrixDet` and `MatrixMath`

![matrix_example](yty_manim/examples/matrix_example.png)

---

#### MatrixCal

A matrix class for absolute control of matrix elements, inheriting from :class:`~.VGroup`,  
- Commonly used for demonstrating matrix computations; each row is a `SquTex`,  
- Supports generating matrices with negative numbers and brackets using :method:`neg_with_brackets`,  
- Get matrix rows using :method:`get_row`,  
- Get matrix columns using :method:`get_column`.

Usage example:

```python
from manim import *
from yty_manim.application.matrix_yty import MatrixCal

class MatrixCalShow(Scene):
    def construct(self):
        m = MatrixCal([[1, -2], [3, 4]])
        self.play(FadeIn(m))
        self.play(Indicate(m.get_row(0)))
        self.wait()
```

---

#### MatrixDet

Determinant calculation, inheriting from :class:`~.MatrixCal`,  
- Commonly used for demonstrating determinant calculations,  
- Supports extended determinant calculation demonstrations using :method:`det_mat`,  
- Automatically adjusts size using :method:`set_scale_fitness`,  
- Get calculation process information using :method:`get_process_inform`,  
- Get result information using :method:`get_result_inform`,  
- Generate calculation steps using :method:`cal_progress_times`,  
- Generate result steps using :method:`cal_result_addition`.

Usage example:

```python
from manim import *
from yty_manim.application.matrix_yty import MatrixDet, matrix_3

class MatrixDetCal(Scene):
    def construct(self):
        mat_mob = MatrixDet(matrix_3)
        mat_mob_det = mat_mob.det_mat()
        vgp, vgp_brackets, num_lst = mat_mob_det.get_process_inform(1)
        self.add(mat_mob_det)
        self.play(FadeIn(vgp), FadeIn(vgp_brackets))
        self.wait()
```

---

#### MatrixMath

Matrix operations, inheriting from :class:`~.MatrixCal`,  
- Used for demonstrating matrix addition / multiplication style workflows,  
- API style mirrors `MatrixDet` for stepwise intermediate results.

Usage example:

```python
from manim import *
from yty_manim.application.matrix_yty import MatrixMath

class MatrixMathShow(Scene):
    def construct(self):
        a = MatrixMath([[1, 2], [3, 4]])
        self.play(FadeIn(a))
        self.wait()
```

---

### page_replacement.py
Contains base classes `Page` / `PageReplacement`, plus  
`OptPageReplacement`, `LruPageReplacement`, `FifoPageReplacement`, and `ClockPageReplacement`  
- Shared stack, frame table, and step interfaces make it easy to plug in more algorithms.

---

#### PageReplacement

OS page-replacement algorithm animation, inheriting from :class:`~.Page`,  
- Access sequence on top, page frames in the middle, optional stack and miss-rate HUD,  
- Use :method:`step_on` to advance; subclasses override :method:`cal_func` for eviction policy,  
- Commonly used to compare OPT / LRU / FIFO / Clock.

Usage example:

```python
from manim import *
from yty_manim.application.page_replacement import OptPageReplacement

class PageOPT(Scene):
    def construct(self):
        input_lst = [7, 0, 1, 2, 0, 3, 0, 4, 2, 3, 0, 3, 2, 1, 2, 0, 1, 7, 0, 1, " "]
        p = OptPageReplacement(input_lst, page_frame_num=3)
        self.add(p)
        self.wait()
        for i in range(len(input_lst) - 1):
            p.step_on(self, i)
```

---

### title_animate.py
Contains class `TitleAnimate`

---

#### TitleAnimate

Title animation, inheriting from :class:`~.SquTexSlide`,  
- Extends sliding blocks into a title intro: push blocks in, then pop them away,  
- Use :method:`generate` to build the title; use :method:`disappear` to tear it down,  
- `force_center` / `force_color` control centering and coloring during pushes.

Usage example:

```python
from manim import *
from yty_manim.application.title_animate import TitleAnimate
from yty_manim.disposition.fonts_and_colors import text_font

class TitleIntroduction(Scene):
    def construct(self):
        ta = TitleAnimate(
            "rainbow",
            font=text_font[0],
            side_length=1.5,
            fill_opacity=0.5,
            stroke_opacity=0.8,
        )
        self.wait()
        ta.generate(self, run_time=0.5)
        self.wait(1)
        ta.disappear(self, run_time=0.2, force_center=False)
        self.wait()
```

---

### s.py
Contains classes `CalculusStep`, `DerivativeVisualizer`, and `IntegralVisualizer`

---

#### CalculusStep

Base class for calculus step visuals, inheriting from :class:`~.VGroup`,  
- Used for teaching derivatives and integrals: plots, tangents, Riemann sums,  
- Use :method:`show_derivative_steps` to get playable derivative steps,  
- Use :method:`show_integral_steps` for integral steps,  
- Use :method:`animate_riemann_sum` to show Riemann-sum convergence,  
- `DerivativeVisualizer` / `IntegralVisualizer` are more specialized wrappers.

Usage example:

```python
from manim import *
from yty_manim.application.s import CalculusStep

class DerivativeShow(Scene):
    def construct(self):
        calc = CalculusStep(lambda x: x ** 2, x_range=[-3, 3])
        self.add(calc)
        for step in calc.show_derivative_steps(x_point=1):
            self.play(*step)
            self.wait(0.5)
```

---

## tools

---

### map_editor

Map editor and shockwave data utilities,  
- `MapBundle` / `ExplosionSource` / `MapMarker` pack walkability, markers, and blast sources,  
- `map_wave.shockwave_field` builds intensity from a Dijkstra / BFS distance field,  
- `map_radar_import` imports walkability from radar images,  
- The Tk GUI can be launched from the repo root.

Usage example:

```bash
python -m yty_manim.tools.map_editor
```

```python
from yty_manim.tools.map_editor import MapBundle, default_maps_dir, shockwave_field

bundle = MapBundle.load(default_maps_dir() / "your_map")
dist, intensity, damage = shockwave_field(bundle)
```

---

## video_project

Production projects.  
- Reusable units live in `yty_manim/basic_unit`  
- Final Manim scenes live under each project's `manim` folder  
- Footage, narration, and edit scripts live under `cs2_c4_footage` / `cs2_c4_edit`, etc.

---

### cs2_c4/manim

CS2 C4 shockwave production scenes. Each file is one or more independently renderable Scenes:

| File | Content |
|------|---------|
| [titles.py](video_project/cs2_c4/manim/titles.py) | TOC + chapter title cards |
| [shockwave.py](video_project/cs2_c4/manim/shockwave.py) | Shockwave algorithm + 3D contrast |
| [pathfinding.py](video_project/cs2_c4/manim/pathfinding.py) | Pathfinding / distance fields |
| [prebake.py](video_project/cs2_c4/manim/prebake.py) | Prebake algorithm |
| [damage_field_3d.py](video_project/cs2_c4/manim/damage_field_3d.py) | 3D damage hill |
| [mirage.py](video_project/cs2_c4/manim/mirage.py) | Mirage multi-shot scenes |

Usage example:

```bash
python -m manim -qh video_project/cs2_c4/manim/titles.py ContentsPageScene
python -m manim -qh video_project/cs2_c4/manim/shockwave.py ShockwaveAlgorithmScene
python -m manim -qh video_project/cs2_c4/manim/pathfinding.py PathfindingAlgorithmsScene
python -m manim -qh video_project/cs2_c4/manim/prebake.py PrebakeAlgorithmScene
python -m manim -qh video_project/cs2_c4/manim/mirage.py MirageShockwaveScene
python -m manim -qh --disable_caching video_project/cs2_c4/manim/damage_field_3d.py ExplosionDamageField3D
```

Rendered clips are typically copied to [cs2_c4_edit/manim](video_project/cs2_c4/cs2_c4_edit/manim); see [render_all.bat](video_project/cs2_c4/cs2_c4_edit/render_all.bat).
