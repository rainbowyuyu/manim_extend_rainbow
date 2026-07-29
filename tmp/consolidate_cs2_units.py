# -*- coding: utf-8 -*-
"""Consolidate CS units into 3 squ_tex-style modules."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(r"d:\python_project\manim_extend_rainbow")
BU = ROOT / "yty_manim" / "basic_unit"
APP = ROOT / "yty_manim" / "application"


def strip_header_and_imports(text: str, drop_import_prefixes: tuple[str, ...] = ()) -> str:
    """Remove rainbow header / future / cross-basic_unit imports; keep body."""
    lines = text.splitlines(True)
    out: list[str] = []
    i = 0
    # skip rainbow banners and short title comments
    while i < len(lines):
        l = lines[i]
        if l.startswith("# rainbow_yu") or (
            i < 5 and l.startswith("# ") and "🐋" not in l and not l.startswith("# ─")
        ):
            i += 1
            continue
        if l.strip() == "" and not out:
            i += 1
            continue
        break
    # optional module docstring keep
    body = "".join(lines[i:])
    # drop from __future__
    body = re.sub(r"^from __future__ import annotations\n+", "", body, count=1, flags=re.M)
    for pref in drop_import_prefixes:
        body = re.sub(
            rf"^from {re.escape(pref)} import .*\n(?:    .*\n)*",
            "",
            body,
            flags=re.M,
        )
        body = re.sub(rf"^from {re.escape(pref)} import \([^)]*\)\n", "", body, flags=re.M | re.S)
    # drop trailing __all__ blocks (we'll rewrite)
    body = re.sub(r"\n__all__ = \([^)]*\)\n?", "\n", body, flags=re.S)
    # drop bfs_path = ... alias lines we'll re-add
    return body.strip() + "\n"


def inject_class_doc(body: str, class_name: str, doc: str) -> str:
    """If class has no/minimal docstring, insert one after class line."""
    pat = rf"(class {class_name}\([^)]*\):\n)(    \"\"\"[\\s\\S]*?\"\"\"\n)?"
    m = re.search(pat, body)
    if not m:
        return body
    # always replace existing short docstring with our squ_tex-style one
    return re.sub(pat, rf"\1{doc}", body, count=1)


ARENA3D_DOC = '''    """
    CS2 C4 风格三维竞技场，
    继承于 :class:`~.VGroup` ，

    Notes
    -----

    - 基于共享 ``GRID`` 玩具地图：地板片 + 合并墙体 + 炸弹/幸存者标记
    - 常与冲击波 / 球体爆炸对比场景一起使用

    Examples
    --------

    >>> class ArenaDemo(ThreeDScene):
    >>>     def construct(self):
    >>>         self.add(Arena3D())
    >>>         self.wait()

    """
'''

GRIDMAP2D_DOC = '''    """
    二维网格地图与寻路可视化，
    继承于 :class:`~.VGroup` ，

    Notes
    -----

    - 与 :class:`Arena3D` 共用 ``GRID`` / ``BOMB_IJ`` / ``SURVIVOR_IJ``
    - 支持按层刷色、路径折线、起终点标记

    Examples
    --------

    >>> class GridDemo(Scene):
    >>>     def construct(self):
    >>>         m = GridMap2D(BOMB_IJ, SURVIVOR_IJ)
    >>>         self.add(m)

    """
'''

EXPLOSION_MARKER_DOC = '''    """
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
'''

DAMAGE_GRID_DOC = '''    """
    预烘焙伤害点阵热力网格，
    继承于 :class:`~.Group` ，

    Notes
    -----

    - 使用 Group 而非 VGroup，避免空锚点 zip 异常
    - 配合 :func:`bake_damage_field` / :func:`bilinear_sample` 使用

    """
'''

DAMAGE_HILL_DOC = '''    """
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
'''

MIRAGE_MAP_DOC = '''    """
    Mirage 矢量俯视地图与流体冲击波前，
    继承于 :class:`~.VGroup` ，

    Notes
    -----

    - 数据来自同模块的可走栅格 / 站点常量
    - 用 :func:`bind_fluid_wave_tracker` 绑定半径追踪器

    """
'''

GRID_MAP_VIEW_DOC = '''    """
    通用 MapBundle 网格地图视图，
    继承于 :class:`~.VGroup` ，

    Notes
    -----

    - 配合 ``tools.map_editor`` 的 bundle / shockwave_field
    - 用 :func:`bind_wave_tracker` / :func:`build_map_view_from_bundle` 装配

    """
'''


def build_cs2_arena() -> str:
    arena = strip_header_and_imports((BU / "arena_3d.py").read_text(encoding="utf-8"))
    # remove leftover scene comment / wrong early stuff already cleaned
    arena = re.sub(r"^from collections import deque\n", "from collections import deque\n", arena)
    pf = strip_header_and_imports(
        (BU / "pathfinding_grid.py").read_text(encoding="utf-8"),
        drop_import_prefixes=("yty_manim.basic_unit.arena_3d",),
    )
    # resolve CELL clash: pathfinding CELL -> CELL_2D
    pf = re.sub(r"^CELL = 0\.52\n", "CELL_2D = 0.52\n", pf, count=1, flags=re.M)
    # replace CELL usages in pathfinding that mean 2d cell — careful not to hit CELL_GAP, CELL_2D
    def repl_cell(m: re.Match) -> str:
        return m.group(0).replace("CELL", "CELL_2D")

    # Only replace standalone CELL token
    pf = re.sub(r"\bCELL\b", "CELL_2D", pf)
    # CELL_2D_GAP mistake if CELL_GAP became CELL_2D_GAP
    pf = pf.replace("CELL_2D_GAP", "CELL_GAP")
    pf = pf.replace("CELL_2D_2D", "CELL_2D")

    arena = inject_class_doc(arena, "Arena3D", ARENA3D_DOC)
    pf = inject_class_doc(pf, "GridMap2D", GRIDMAP2D_DOC)

    header = '''# rainbow_yu manim_extend.basic_unit.cs2_arena 🐋✨
# CS2 玩具竞技场：三维 Arena + 二维寻路网格

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
import heapq

import numpy as np
from manim import *

from yty_manim.disposition.fonts_and_colors import text_font

__all__ = (
    "GRID",
    "BOMB_IJ",
    "SURVIVOR_IJ",
    "CELL",
    "CELL_2D",
    "FLOOR_H",
    "WALL_H",
    "MAP_SCALE",
    "MAP_SHIFT",
    "Arena3D",
    "GridMap2D",
    "AlgoSpec",
    "FormulaLine",
    "DeepDive",
    "bfs_path",
    "bfs_dist",
    "intensity_to_hp",
)


'''
    # strip duplicate imports from arena body
    arena = re.sub(r"^from collections import deque\n", "", arena, count=1, flags=re.M)
    arena = re.sub(r"^import numpy as np\n", "", arena, count=1, flags=re.M)
    arena = re.sub(r"^from manim import \*\n", "", arena, count=1, flags=re.M)
    arena = re.sub(
        r"^from yty_manim\.disposition\.fonts_and_colors import text_font\n",
        "",
        arena,
        count=1,
        flags=re.M,
    )
    pf = re.sub(r"^import heapq\n", "", pf, count=1, flags=re.M)
    pf = re.sub(r"^from collections import deque\n", "", pf, count=1, flags=re.M)
    pf = re.sub(r"^from dataclasses import dataclass, field\n", "", pf, count=1, flags=re.M)
    pf = re.sub(r"^import numpy as np\n", "", pf, count=1, flags=re.M)
    pf = re.sub(r"^from manim import \*\n", "", pf, count=1, flags=re.M)
    pf = re.sub(
        r"^from yty_manim\.disposition\.fonts_and_colors import text_font\n",
        "",
        pf,
        count=1,
        flags=re.M,
    )

    # public aliases for bfs
    if "bfs_path =" not in arena:
        arena += "\nbfs_path = _bfs_path\nbfs_dist = _bfs_dist\n"
    else:
        arena = arena.replace("bfs_path = _bfs_path", "bfs_path = _bfs_path\nbfs_dist = _bfs_dist")

    # compat: many demos import CELL from pathfinding meaning CELL_2D
    pf += "\n# 兼容：旧路径寻路代码里的 CELL 即二维格子边长\nCELL = CELL_2D\n"

    return header + "\n# ── 三维竞技场 ──────────────────────────────────────────────\n\n" + arena + "\n# ── 二维寻路网格 ────────────────────────────────────────────\n\n" + pf


def build_cs2_damage() -> str:
    heat = strip_header_and_imports((BU / "map_heat.py").read_text(encoding="utf-8"))
    heat = re.sub(r"^import numpy as np\n", "", heat, count=1, flags=re.M)
    heat = re.sub(r"^from manim import \*\n", "", heat, count=1, flags=re.M)
    heat = re.sub(r"^from __future__ import annotations\n", "", heat, count=1, flags=re.M)

    pre = strip_header_and_imports((BU / "explosion_prebake.py").read_text(encoding="utf-8"))
    pre = re.sub(r"^from dataclasses import dataclass\n", "", pre, count=1, flags=re.M)
    pre = re.sub(r"^import numpy as np\n", "", pre, count=1, flags=re.M)
    pre = re.sub(r"^from manim import \*\n", "", pre, count=1, flags=re.M)
    pre = re.sub(
        r"^from yty_manim\.disposition\.fonts_and_colors import text_font\n",
        "",
        pre,
        count=1,
        flags=re.M,
    )
    # remove trailing alias if present; re-add once
    pre = re.sub(r"\n# 兼容旧名.*\nExplosionSource = ExplosionMarker\n?", "\n", pre)
    pre = inject_class_doc(pre, "ExplosionMarker", EXPLOSION_MARKER_DOC)
    pre = inject_class_doc(pre, "DamageGrid", DAMAGE_GRID_DOC)

    field = strip_header_and_imports((BU / "damage_field_3d.py").read_text(encoding="utf-8"))
    field = re.sub(r"^import numpy as np\n", "", field, count=1, flags=re.M)
    field = re.sub(r"^from manim import \*\n", "", field, count=1, flags=re.M)

    # Wrap field helpers into DamageHill3D class while keeping module-level aliases for demos
    hill = '''
class DamageHill3D:
''' + DAMAGE_HILL_DOC + '''
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


# 兼容 Scene 中旧的函数式调用
def height(x: float, y: float) -> float:
    return DamageHill3D().height(x, y)

'''
    # Keep original _height etc.; demo uses _height from import *
    # Add aliases without breaking:
    field = field + hill
    field += """
# 旧名兼容（explosion_damage_field_3d_demo）
_height = height
"""

    header = '''# rainbow_yu manim_extend.basic_unit.cs2_damage 🐋✨
# CS2 爆炸伤害：预烘焙教学组件 + 三维伤害丘

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from manim import *

from yty_manim.disposition.fonts_and_colors import text_font

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


'''
    return (
        header
        + "\n# ── 热力着色 ────────────────────────────────────────────────\n\n"
        + heat
        + "\n# ── 预烘焙教学组件 ──────────────────────────────────────────\n\n"
        + pre
        + "\nExplosionSource = ExplosionMarker\n"
        + "\n# ── 三维伤害丘 ──────────────────────────────────────────────\n\n"
        + field
    )


def build_cs2_map() -> str:
    snip = strip_header_and_imports((BU / "cs2_snippets.py").read_text(encoding="utf-8"))
    data = strip_header_and_imports((BU / "mirage_data.py").read_text(encoding="utf-8"))
    overview = strip_header_and_imports((BU / "mirage_overview.py").read_text(encoding="utf-8"))
    mmap = strip_header_and_imports(
        (BU / "mirage_map.py").read_text(encoding="utf-8"),
        drop_import_prefixes=(
            "yty_manim.basic_unit.map_heat",
            "yty_manim.basic_unit.mirage_data",
        ),
    )
    gview = strip_header_and_imports(
        (BU / "grid_map_view.py").read_text(encoding="utf-8"),
        drop_import_prefixes=(
            "yty_manim.basic_unit.map_heat",
        ),
    )

    # dedupe WAVE_SPEED in data if snippets already has it — keep data's with CELL_METERS context;
    # remove from snippets duplicate by leaving both (same value) — remove snip's if present after merge by comment
    # Remove duplicate rgb_to_hex / intensity_color wrappers in gview — use shared defs

    # Clean imports from parts
    for name, part in [("snip", snip), ("data", data), ("overview", overview), ("mmap", mmap), ("gview", gview)]:
        pass

    data = re.sub(r"^import heapq\n", "", data, count=1, flags=re.M)
    data = re.sub(r"^import json\n", "", data, count=1, flags=re.M)
    data = re.sub(r"^from dataclasses import dataclass\n", "", data, count=1, flags=re.M)
    data = re.sub(r"^from pathlib import Path\n", "", data, count=1, flags=re.M)
    data = re.sub(r"^import numpy as np\n", "", data, count=1, flags=re.M)

    overview = re.sub(r"^import re\n", "", overview, count=1, flags=re.M)
    overview = re.sub(r"^from dataclasses import dataclass\n", "", overview, count=1, flags=re.M)
    overview = re.sub(r"^from pathlib import Path\n", "", overview, count=1, flags=re.M)

    mmap = re.sub(r"^import numpy as np\n", "", mmap, count=1, flags=re.M)
    mmap = re.sub(r"^from manim import \*\n", "", mmap, count=1, flags=re.M)
    mmap = re.sub(r"^from scipy\.ndimage import zoom\n", "", mmap, count=1, flags=re.M)
    # local intensity uses intensity_color — provide module-level intensity_color from heat inline
    mmap = inject_class_doc(mmap, "MirageVectorMap", MIRAGE_MAP_DOC)

    gview = re.sub(r"^import numpy as np\n", "", gview, count=1, flags=re.M)
    gview = re.sub(r"^from manim import \*\n", "", gview, count=1, flags=re.M)
    # remove local intensity_color / rgb_to_hex if data has rgb_to_hex — keep gview intensity as thin wrapper
    gview = inject_class_doc(gview, "GridMapView", GRID_MAP_VIEW_DOC)
    # Fix _heat_intensity reference — use intensity_color defined in this module
    gview = gview.replace(
        "return _heat_intensity(t, cool=C_WAVE_COOL, mid=C_WAVE_MID, hot=C_WAVE_HOT, zero=C_WALK)",
        "return intensity_color(t, cool=C_WAVE_COOL, mid=C_WAVE_MID, hot=C_WAVE_HOT, zero=C_WALK)",
    )
    # If gview still defines its own intensity_color function, rename conflict with heat's
    # We'll put intensity_color once before maps

    heat_fn = '''
def intensity_color(
    t: float,
    *,
    cool: str = "#4ecdc4",
    mid: str = "#f7c548",
    hot: str = "#ff6b35",
    zero: str | None = "#1a2332",
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

'''

    # Remove duplicate WAVE_SPEED_M_S from snip if data also defines — keep in data section only
    snip = re.sub(r"^WAVE_SPEED_M_S = 27\.5\n", "", snip, flags=re.M)

    # Remove duplicate intensity_color def in gview (the whole function)
    gview = re.sub(
        r"\ndef intensity_color\(t: float\) -> str:\n(?:    .*\n)+",
        "\ndef _bundle_intensity_color(t: float) -> str:\n"
        "    return intensity_color(t, cool=C_WAVE_COOL, mid=C_WAVE_MID, hot=C_WAVE_HOT, zero=C_WALK)\n\n",
        gview,
        count=1,
    )
    gview = gview.replace("intensity_color(", "_bundle_intensity_color(").replace(
        "def _bundle_intensity_color(t: float) -> str:\n    return _bundle_intensity_color(",
        "def _bundle_intensity_color(t: float) -> str:\n    return intensity_color(",
    )
    # fix over-replace on def line body - do carefully
    # Actually the replace_all intensity_color( -> _bundle might break the return intensity_color inside.
    # Re-read approach: leave gview intensity as alias

    # Simpler: delete gview's intensity_color function entirely and replace calls with intensity_color(...)
    # Re-do gview intensity handling more carefully
    gview_raw = strip_header_and_imports(
        (BU / "grid_map_view.py").read_text(encoding="utf-8"),
        drop_import_prefixes=("yty_manim.basic_unit.map_heat",),
    )
    gview_raw = re.sub(r"^import numpy as np\n", "", gview_raw, count=1, flags=re.M)
    gview_raw = re.sub(r"^from manim import \*\n", "", gview_raw, count=1, flags=re.M)
    gview_raw = re.sub(
        r"from yty_manim\.tools\.map_editor\.map_bundle import ExplosionSource, MapBundle, MapMarker\n",
        "from yty_manim.tools.map_editor.map_bundle import ExplosionSource, MapBundle, MapMarker\n",
        gview_raw,
    )
    # remove local intensity_color function
    gview_raw = re.sub(
        r"\ndef intensity_color\(t: float\) -> str:\n(?:    .*\n)+?",
        "\n",
        gview_raw,
        count=1,
    )
    # remove rgb_to_hex if we'll keep data's — mirage_data has rgb_to_hex; gview also — keep first in data, remove from gview
    gview_raw = re.sub(
        r"\ndef rgb_to_hex\(r: int, g: int, b: int\) -> str:\n    return f\"#\{r:02x\}\{g:02x\}\{b:02x\}\"\n",
        "\n",
        gview_raw,
        count=1,
    )
    gview_raw = gview_raw.replace(
        "return _heat_intensity(t, cool=C_WAVE_COOL, mid=C_WAVE_MID, hot=C_WAVE_HOT, zero=C_WALK)",
        "return intensity_color(t, cool=C_WAVE_COOL, mid=C_WAVE_MID, hot=C_WAVE_HOT, zero=C_WALK)",
    )
    # If old body still has if t<=0 style after botched earlier edit - the source file might still have old
    # After removing intensity_color, GridMapView methods that call intensity_color still work with module-level fn
    gview = inject_class_doc(gview_raw, "GridMapView", GRID_MAP_VIEW_DOC)

    header = '''# rainbow_yu manim_extend.basic_unit.cs2_map 🐋✨
# CS2 地图：Mirage 数据/渲染、MapBundle 视图、引擎文案常量

from __future__ import annotations

import heapq
import json
import re
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from manim import *
from scipy.ndimage import zoom

from yty_manim.tools.map_editor.map_bundle import ExplosionSource, MapBundle, MapMarker
from yty_manim.tools.map_editor.map_wave import shockwave_field

__all__ = (
    "WAVE_SPEED_M_S",
    "intensity_color",
    "MirageVectorMap",
    "GridMapView",
    "MirageOverview",
    "MapSite",
    "bind_fluid_wave_tracker",
    "bind_wave_tracker",
    "build_map_view_from_bundle",
    "load_mirage_overview",
    "shockwave_field",
    "dijkstra_wave_field",
    "arrival_time_seconds",
)


'''
    # Remove duplicate imports from gview body
    gview = re.sub(
        r"^from yty_manim\.tools\.map_editor\.map_bundle import ExplosionSource, MapBundle, MapMarker\n",
        "",
        gview,
        count=1,
        flags=re.M,
    )
    gview = re.sub(
        r"^from yty_manim\.tools\.map_editor\.map_wave import shockwave_field\n",
        "",
        gview,
        count=1,
        flags=re.M,
    )

    # mirage_map _intensity_color already wraps intensity_color — good once heat_fn is above

    # snippets may still import nothing
    return (
        header
        + "\n# ── 引擎文案常量 ────────────────────────────────────────────\n\n"
        + snip
        + "\n# ── 热力着色 ────────────────────────────────────────────────\n\n"
        + heat_fn
        + "\n# ── Mirage 数据 ──────────────────────────────────────────────\n\n"
        + data
        + "\n# ── Overview 坐标 ────────────────────────────────────────────\n\n"
        + overview
        + "\n# ── Mirage 矢量地图 ──────────────────────────────────────────\n\n"
        + mmap
        + "\n# ── MapBundle 网格视图 ───────────────────────────────────────\n\n"
        + gview
    )


def update_application_imports() -> None:
    replacements = {
        APP / "cs2_bomb_3d_demo.py": [
            ("from yty_manim.basic_unit.arena_3d import *  # noqa: F401,F403",
             "from yty_manim.basic_unit.cs2_arena import *  # noqa: F401,F403"),
        ],
        APP / "pathfinding_algorithms_demo.py": [
            ("from yty_manim.basic_unit.pathfinding_grid import *  # noqa: F401,F403",
             "from yty_manim.basic_unit.cs2_arena import *  # noqa: F401,F403"),
        ],
        APP / "shockwave_algorithm_demo.py": [
            ("from yty_manim.basic_unit.arena_3d import (",
             "from yty_manim.basic_unit.cs2_arena import ("),
            ("from yty_manim.basic_unit.cs2_snippets import WAVE_SPEED_M_S",
             "from yty_manim.basic_unit.cs2_map import WAVE_SPEED_M_S"),
            ("from yty_manim.basic_unit.pathfinding_grid import (",
             "from yty_manim.basic_unit.cs2_arena import ("),
        ],
        APP / "prebake_algorithm_demo.py": [
            ("from yty_manim.basic_unit.arena_3d import BOMB_IJ, GRID, SURVIVOR_IJ",
             "from yty_manim.basic_unit.cs2_arena import BOMB_IJ, GRID, SURVIVOR_IJ"),
            ("from yty_manim.basic_unit.explosion_prebake import (",
             "from yty_manim.basic_unit.cs2_damage import ("),
            ("from yty_manim.basic_unit.mirage_data import WAVE_SPEED_M_S, arrival_time_seconds",
             "from yty_manim.basic_unit.cs2_map import WAVE_SPEED_M_S, arrival_time_seconds"),
        ],
        APP / "explosion_prebake_viz.py": [
            ("from yty_manim.basic_unit.explosion_prebake import (",
             "from yty_manim.basic_unit.cs2_damage import ("),
        ],
        APP / "explosion_damage_field_3d_demo.py": [
            ("from yty_manim.basic_unit.damage_field_3d import *  # noqa: F401,F403",
             "from yty_manim.basic_unit.cs2_damage import *  # noqa: F401,F403"),
        ],
        APP / "cs2_bomb_wave.py": [
            ("from yty_manim.basic_unit.cs2_snippets import (",
             "from yty_manim.basic_unit.cs2_map import ("),
            ("from yty_manim.basic_unit.mirage_data import (",
             "from yty_manim.basic_unit.cs2_map import ("),
            ("from yty_manim.basic_unit.mirage_map import MirageVectorMap, bind_fluid_wave_tracker",
             "from yty_manim.basic_unit.cs2_map import MirageVectorMap, bind_fluid_wave_tracker"),
        ],
        APP / "map_shockwave_scene.py": [
            ("from yty_manim.basic_unit.grid_map_view import bind_wave_tracker, build_map_view_from_bundle",
             "from yty_manim.basic_unit.cs2_map import bind_wave_tracker, build_map_view_from_bundle"),
        ],
    }
    # cs2_bomb_wave may get duplicate imports from cs2_map — merge later if needed
    for path, pairs in replacements.items():
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        for a, b in pairs:
            text = text.replace(a, b)
        path.write_text(text, encoding="utf-8")
        print("updated", path.name)

    # Fix cs2_bomb_wave: two imports from cs2_map — consolidate
    wave = APP / "cs2_bomb_wave.py"
    t = wave.read_text(encoding="utf-8")
    # leave as-is if two blocks; Python allows. Optional merge skipped.

    # video_project script
    br = ROOT / "video_project" / "cs2_c4" / "cs2_c4_data" / "build_radar_walkability.py"
    if br.exists():
        bt = br.read_text(encoding="utf-8")
        bt2 = bt.replace(
            "from yty_manim.application.mirage_overview import load_mirage_overview",
            "from yty_manim.basic_unit.cs2_map import load_mirage_overview",
        )
        if bt2 != bt:
            br.write_text(bt2, encoding="utf-8")
            print("updated build_radar_walkability")


def delete_old() -> None:
    old_bu = [
        "arena_3d.py",
        "pathfinding_grid.py",
        "explosion_prebake.py",
        "damage_field_3d.py",
        "map_heat.py",
        "cs2_snippets.py",
        "mirage_data.py",
        "mirage_map.py",
        "mirage_overview.py",
        "grid_map_view.py",
    ]
    old_app = [
        "explosion_prebake_core.py",
        "cs2_source_snippets.py",
        "map_render.py",
        "mirage_map_data.py",
        "mirage_vector_map.py",
        "mirage_overview.py",
    ]
    for n in old_bu:
        p = BU / n
        if p.exists():
            p.unlink()
            print("del", p.name)
    for n in old_app:
        p = APP / n
        if p.exists():
            p.unlink()
            print("del app", p.name)


def write_init() -> None:
    (BU / "__init__.py").write_text(
        '''# rainbow_yu manim_extend.basic_unit 🐋✨

__version__ = '0.7.1'

__all__ = (
    "dec_bin",
    "squ_tex",
    "threed_vgp",
    "screen_cycle",
    "code_step",
    "shapes",
    "cs2_arena",
    "cs2_damage",
    "cs2_map",
)

from .dec_bin import *
from .squ_tex import *
from .threed_vgp import *
from .screen_cycle import *
from .code_step import *
from .shapes import *

from . import cs2_arena
from . import cs2_damage
from . import cs2_map
''',
        encoding="utf-8",
    )
    print("wrote __init__")


def fix_cs2_bomb_wave_imports() -> None:
    """Merge duplicate cs2_map import blocks if present."""
    path = APP / "cs2_bomb_wave.py"
    text = path.read_text(encoding="utf-8")
    # If there are two 'from yty_manim.basic_unit.cs2_map import' — leave; ast will work
    # Deduplicate WAVE names by combining is optional
    path.write_text(text, encoding="utf-8")


def main() -> None:
    (BU / "cs2_arena.py").write_text(build_cs2_arena(), encoding="utf-8")
    print("wrote cs2_arena", len((BU / "cs2_arena.py").read_text(encoding="utf-8").splitlines()))
    (BU / "cs2_damage.py").write_text(build_cs2_damage(), encoding="utf-8")
    print("wrote cs2_damage", len((BU / "cs2_damage.py").read_text(encoding="utf-8").splitlines()))
    (BU / "cs2_map.py").write_text(build_cs2_map(), encoding="utf-8")
    print("wrote cs2_map", len((BU / "cs2_map.py").read_text(encoding="utf-8").splitlines()))
    update_application_imports()
    fix_cs2_bomb_wave_imports()
    delete_old()
    write_init()
    print("DONE")


if __name__ == "__main__":
    main()
