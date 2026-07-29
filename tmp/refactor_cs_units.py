# -*- coding: utf-8 -*-
"""One-shot refactor: move CS/map/explosion units into basic_unit."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(r"d:\python_project\manim_extend_rainbow")
BU = ROOT / "yty_manim" / "basic_unit"
APP = ROOT / "yty_manim" / "application"


def set_header(path: Path, module: str, title: str) -> None:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines(True)
    if lines and "manim_extend.basic_unit." in lines[0]:
        return
    while lines and lines[0].startswith("# rainbow_yu"):
        lines.pop(0)
        while lines and lines[0].strip() == "":
            lines.pop(0)
        # drop one short descriptive comment line after banner if present
        if lines and lines[0].startswith("#") and not lines[0].startswith('"""'):
            # keep file docstring; only drop single-line banner follow-ups that look like titles
            if not lines[0].startswith("# ─") and len(lines[0]) < 100 and "Usage" not in lines[0]:
                # keep Chinese description comments — actually leave them
                pass
        break
    header = f"# rainbow_yu manim_extend.basic_unit.{module} 🐋✨\n# {title}\n\n"
    path.write_text(header + "".join(lines), encoding="utf-8")
    print("header", path.name)


def main() -> None:
    set_header(BU / "explosion_prebake.py", "explosion_prebake", "爆炸伤害预烘焙：算法与可视化组件")
    set_header(BU / "cs2_snippets.py", "cs2_snippets", "CS2 爆炸相关伪代码与常量文案")
    set_header(BU / "grid_map_view.py", "grid_map_view", "通用 MapBundle 网格地图渲染")
    set_header(BU / "mirage_data.py", "mirage_data", "Mirage 地图数据与冲击波场")
    set_header(BU / "mirage_map.py", "mirage_map", "Mirage 矢量地图与流体波前")
    set_header(BU / "mirage_overview.py", "mirage_overview", "Mirage 总览 SVG/栅格工具")

    # mirage_map import
    p = BU / "mirage_map.py"
    t = p.read_text(encoding="utf-8")
    t = t.replace(
        "from yty_manim.application.mirage_map_data import",
        "from yty_manim.basic_unit.mirage_data import",
    )
    p.write_text(t, encoding="utf-8")
    print("fixed mirage_map import")

    # ExplosionMarker alias
    p = BU / "explosion_prebake.py"
    t = p.read_text(encoding="utf-8")
    t = t.replace("class ExplosionSource(VGroup):", "class ExplosionMarker(VGroup):")
    if "ExplosionSource = ExplosionMarker" not in t:
        t = t.rstrip() + "\n\n# 兼容旧名（教学爆炸标记，非 map_bundle.ExplosionSource）\nExplosionSource = ExplosionMarker\n"
    p.write_text(t, encoding="utf-8")
    print("ExplosionMarker alias")

    # --- arena_3d ---
    src_lines = (APP / "cs2_bomb_3d_demo.py").read_text(encoding="utf-8").splitlines(True)
    # If already thinned, skip
    if any("from yty_manim.basic_unit.arena_3d" in l for l in src_lines[:40]):
        print("cs2_bomb_3d_demo already thinned; skip arena extract")
    else:
        idx = next(i for i, l in enumerate(src_lines) if l.startswith("class OldBombSphere3DScene"))
        start = next(i for i, l in enumerate(src_lines) if l.startswith("from __future__"))
        arena_body = "".join(src_lines[start:idx])
        # discover bfs name
        m = re.search(r"^def (\w*bfs\w*)\(", arena_body, re.M)
        bfs_name = m.group(1) if m else "bfs_shortest_path"
        print("bfs fn", bfs_name)
        # public alias
        if "def bfs_path(" not in arena_body and bfs_name != "bfs_path":
            arena_body += f"\n\nbfs_path = {bfs_name}\n"
        arena_body += """
__all__ = (
    "GRID",
    "BOMB_IJ",
    "SURVIVOR_IJ",
    "BLOCKED_IJ",
    "Arena3D",
    "UI_FONT",
    "bfs_path",
    "_damage_color",
    "_intensity_from_dist",
    "_merged_wall_rects",
    "_set_tile_color",
    "_hud_title",
    "_wire_sphere",
)
"""
        (BU / "arena_3d.py").write_text(
            "# rainbow_yu manim_extend.basic_unit.arena_3d 🐋✨\n"
            "# CS2 C4 风格三维竞技场：GRID / Arena3D / BFS 路径\n\n"
            + arena_body,
            encoding="utf-8",
        )
        print("wrote arena_3d")

        scene_part = "".join(src_lines[idx:])
        thin = '''# rainbow_yu — CS2 C4 3D explosion demos (old sphere vs new BFS wave)
"""Two cinematic ThreeDScenes on a shared stylized arena map.

Usage:
    python -m manim -qh yty_manim/application/cs2_bomb_3d_demo.py OldBombSphere3DScene
    python -m manim -qh yty_manim/application/cs2_bomb_3d_demo.py NewBombSearch3DScene
"""

from __future__ import annotations

from manim import *

from yty_manim.basic_unit.arena_3d import *  # noqa: F401,F403

__all__ = (
    "OldBombSphere3DScene",
    "NewBombSearch3DScene",
    "GRID",
    "BOMB_IJ",
    "SURVIVOR_IJ",
    "Arena3D",
)


'''
        (APP / "cs2_bomb_3d_demo.py").write_text(thin + scene_part, encoding="utf-8")
        print("thinned cs2_bomb_3d_demo")

    # --- pathfinding_grid ---
    pf_path = APP / "pathfinding_algorithms_demo.py"
    pf_lines = pf_path.read_text(encoding="utf-8").splitlines(True)
    if any("from yty_manim.basic_unit.pathfinding_grid" in l for l in pf_lines[:40]):
        print("pathfinding already thinned")
    else:
        idx = next(i for i, l in enumerate(pf_lines) if l.startswith("class PathfindingAlgorithmsScene"))
        # Keep scene-local UI helpers in application; move core through GridMap2D
        # Everything before PathfindingAlgorithmsScene goes to basic_unit except title import
        start = next(i for i, l in enumerate(pf_lines) if l.startswith("from __future__"))
        core = "".join(pf_lines[start:idx])
        core = core.replace(
            "from yty_manim.application.cs2_bomb_3d_demo import BOMB_IJ, GRID, SURVIVOR_IJ",
            "from yty_manim.basic_unit.arena_3d import BOMB_IJ, GRID, SURVIVOR_IJ",
        )
        # drop title demo import from basic unit
        core = re.sub(
            r"from yty_manim\.application\.pathfinding_title_demo import.*\n",
            "",
            core,
        )
        core = re.sub(
            r'^__all__ = \("PathfindingAlgorithmsScene",\)\n',
            "",
            core,
            flags=re.M,
        )
        # drop scene-only helpers that stay more useful in app? Keep all visual helpers in basic_unit
        # for reuse; Scene will import them.
        (BU / "pathfinding_grid.py").write_text(
            "# rainbow_yu manim_extend.basic_unit.pathfinding_grid 🐋✨\n"
            "# 二维网格地图与寻路/距离场算法可视化单元\n\n"
            + core
            + "\n",
            encoding="utf-8",
        )
        print("wrote pathfinding_grid")

        scene_part = "".join(pf_lines[idx:])
        thin = '''# rainbow_yu — 2D pathfinding / distance-field algorithm showcase (CS2 C4 extension)
"""Integrated explainer: title overview + Euclidean / BFS / Dijkstra / A* / Manhattan / Greedy.

Usage:
    python -m manim -qh yty_manim/application/pathfinding_algorithms_demo.py PathfindingAlgorithmsScene
"""

from __future__ import annotations

from manim import *

from yty_manim.application.pathfinding_title_demo import play_pathfinding_title_card
from yty_manim.basic_unit.pathfinding_grid import *  # noqa: F401,F403

__all__ = ("PathfindingAlgorithmsScene",)


'''
        pf_path.write_text(thin + scene_part, encoding="utf-8")
        print("thinned pathfinding_algorithms_demo")

    # --- damage_field_3d ---
    df_path = APP / "explosion_damage_field_3d_demo.py"
    df_lines = df_path.read_text(encoding="utf-8").splitlines(True)
    if any("from yty_manim.basic_unit.damage_field_3d" in l for l in df_lines[:30]):
        print("damage field already thinned")
    else:
        idx = next(i for i, l in enumerate(df_lines) if l.startswith("class ExplosionDamageField3D"))
        start = next(i for i, l in enumerate(df_lines) if l.startswith("from __future__"))
        core = "".join(df_lines[start:idx])
        core = re.sub(r'^__all__ = \("ExplosionDamageField3D",\)\n', "", core, flags=re.M)
        (BU / "damage_field_3d.py").write_text(
            "# rainbow_yu manim_extend.basic_unit.damage_field_3d 🐋✨\n"
            "# 三维爆炸伤害丘曲面、着色与下滑轨迹\n\n"
            + core
            + "\n",
            encoding="utf-8",
        )
        scene_part = "".join(df_lines[idx:])
        thin = '''# rainbow_yu — 3D 爆炸伤害场 · 梯度下降采样点
"""C4 风格伤害丘：中心致死圈 + 外圈衰减；红→绿蓝高度渐变；弯曲下滑轨迹。

Usage:
    python -m manim -qh --disable_caching \\
        yty_manim/application/explosion_damage_field_3d_demo.py ExplosionDamageField3D
"""

from __future__ import annotations

from manim import *

from yty_manim.basic_unit.damage_field_3d import *  # noqa: F401,F403

__all__ = ("ExplosionDamageField3D",)


'''
        df_path.write_text(thin + scene_part, encoding="utf-8")
        print("wrote damage_field_3d + thinned demo")

    # --- map_heat shared intensity ---
    heat = '''# rainbow_yu manim_extend.basic_unit.map_heat 🐋✨
# 地图/冲击波强度着色

from __future__ import annotations

import numpy as np
from manim import *


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


__all__ = ("intensity_color",)
'''
    (BU / "map_heat.py").write_text(heat, encoding="utf-8")
    print("wrote map_heat")

    # Optional: wire mirage_map to use map_heat
    p = BU / "mirage_map.py"
    t = p.read_text(encoding="utf-8")
    if "from yty_manim.basic_unit.map_heat import" not in t:
        t = t.replace(
            "from yty_manim.basic_unit.mirage_data import (",
            "from yty_manim.basic_unit.map_heat import intensity_color\n"
            "from yty_manim.basic_unit.mirage_data import (",
        )
        # replace local _intensity_color body with wrapper
        t = re.sub(
            r"def _intensity_color\(t: float\) -> str:\n(?:    .*\n)+?",
            "def _intensity_color(t: float) -> str:\n"
            "    return intensity_color(t, cool=C_WAVE_COOL, mid=C_WAVE_MID, hot=C_WAVE_HOT, zero=C_WALK)\n\n",
            t,
            count=1,
        )
        p.write_text(t, encoding="utf-8")
        print("wired mirage_map to map_heat")

    # --- application shims ---
    shims = {
        "explosion_prebake_core.py": '''# rainbow_yu — shim → basic_unit.explosion_prebake
"""兼容旧导入路径。"""
from yty_manim.basic_unit.explosion_prebake import *  # noqa: F401,F403
''',
        "cs2_source_snippets.py": '''# rainbow_yu — shim → basic_unit.cs2_snippets
"""兼容旧导入路径。"""
from yty_manim.basic_unit.cs2_snippets import *  # noqa: F401,F403
''',
        "map_render.py": '''# rainbow_yu — shim → basic_unit.grid_map_view
"""兼容旧导入路径。"""
from yty_manim.basic_unit.grid_map_view import *  # noqa: F401,F403
''',
        "mirage_map_data.py": '''# rainbow_yu — shim → basic_unit.mirage_data
"""兼容旧导入路径。"""
from yty_manim.basic_unit.mirage_data import *  # noqa: F401,F403
''',
        "mirage_vector_map.py": '''# rainbow_yu — shim → basic_unit.mirage_map
"""兼容旧导入路径。"""
from yty_manim.basic_unit.mirage_map import *  # noqa: F401,F403
''',
        "mirage_overview.py": '''# rainbow_yu — shim → basic_unit.mirage_overview
"""兼容旧导入路径。"""
from yty_manim.basic_unit.mirage_overview import *  # noqa: F401,F403
''',
    }
    for name, content in shims.items():
        (APP / name).write_text(content, encoding="utf-8")
        print("shim", name)

    # Update application imports that should prefer basic_unit (optional but cleaner)
    replacements = [
        (
            APP / "prebake_algorithm_demo.py",
            [
                (
                    "from yty_manim.application.cs2_bomb_3d_demo import BOMB_IJ, GRID, SURVIVOR_IJ",
                    "from yty_manim.basic_unit.arena_3d import BOMB_IJ, GRID, SURVIVOR_IJ",
                ),
                (
                    "from yty_manim.application.explosion_prebake_core import",
                    "from yty_manim.basic_unit.explosion_prebake import",
                ),
                (
                    "from yty_manim.application.mirage_map_data import WAVE_SPEED_M_S, arrival_time_seconds",
                    "from yty_manim.basic_unit.mirage_data import WAVE_SPEED_M_S, arrival_time_seconds",
                ),
            ],
        ),
        (
            APP / "explosion_prebake_viz.py",
            [
                (
                    "from yty_manim.application.explosion_prebake_core import",
                    "from yty_manim.basic_unit.explosion_prebake import",
                ),
            ],
        ),
        (
            APP / "shockwave_algorithm_demo.py",
            [
                (
                    "from yty_manim.application.cs2_bomb_3d_demo import (",
                    "from yty_manim.basic_unit.arena_3d import (",
                ),
                (
                    "from yty_manim.application.cs2_source_snippets import WAVE_SPEED_M_S",
                    "from yty_manim.basic_unit.cs2_snippets import WAVE_SPEED_M_S",
                ),
            ],
        ),
        (
            APP / "cs2_bomb_wave.py",
            [
                (
                    "from yty_manim.application.cs2_source_snippets import (",
                    "from yty_manim.basic_unit.cs2_snippets import (",
                ),
                (
                    "from yty_manim.application.mirage_map_data import (",
                    "from yty_manim.basic_unit.mirage_data import (",
                ),
                (
                    "from yty_manim.application.mirage_vector_map import MirageVectorMap, bind_fluid_wave_tracker",
                    "from yty_manim.basic_unit.mirage_map import MirageVectorMap, bind_fluid_wave_tracker",
                ),
            ],
        ),
        (
            APP / "map_shockwave_scene.py",
            [
                (
                    "from yty_manim.application.map_render import bind_wave_tracker, build_map_view_from_bundle",
                    "from yty_manim.basic_unit.grid_map_view import bind_wave_tracker, build_map_view_from_bundle",
                ),
            ],
        ),
    ]
    for path, pairs in replacements:
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        for a, b in pairs:
            if a in text:
                text = text.replace(a, b)
                print("rewrote import in", path.name)
        path.write_text(text, encoding="utf-8")

    # basic_unit __init__
    init = '''# rainbow_yu manim_extend.basic_unit 🐋✨

__version__ = '0.7.0'

__all__ = (
    "dec_bin",
    "squ_tex",
    "threed_vgp",
    "screen_cycle",
    "code_step",
    "shapes",
    "explosion_prebake",
    "arena_3d",
    "pathfinding_grid",
    "grid_map_view",
    "mirage_data",
    "mirage_map",
    "mirage_overview",
    "damage_field_3d",
    "cs2_snippets",
    "map_heat",
)

from .dec_bin import *
from .squ_tex import *
from .threed_vgp import *
from .screen_cycle import *
from .code_step import *
from .shapes import *
from .explosion_prebake import *
from .arena_3d import *
from .pathfinding_grid import *
from .grid_map_view import *
from .mirage_data import *
from .mirage_map import *
from .mirage_overview import *
from .damage_field_3d import *
from .cs2_snippets import *
from .map_heat import *
'''
    (BU / "__init__.py").write_text(init, encoding="utf-8")
    print("updated basic_unit/__init__.py")
    print("DONE")


if __name__ == "__main__":
    main()
