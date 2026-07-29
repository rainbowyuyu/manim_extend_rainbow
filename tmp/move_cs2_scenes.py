# -*- coding: utf-8 -*-
"""Move CS2 Manim scenes from application → video_project/cs2_c4/manim (no demo names)."""
from __future__ import annotations

import re
import shutil
from pathlib import Path

ROOT = Path(r"d:\python_project\manim_extend_rainbow")
APP = ROOT / "yty_manim" / "application"
DEST = ROOT / "video_project" / "cs2_c4" / "manim"


def read(name: str) -> str:
    return (APP / name).read_text(encoding="utf-8")


def strip_module_banner(text: str) -> str:
    """Drop leading rainbow/Usage docstring block until first from/import/__future__/class/def."""
    lines = text.splitlines(True)
    i = 0
    # skip comments and blank and one docstring
    while i < len(lines):
        s = lines[i]
        if s.startswith("#") or s.strip() == "":
            i += 1
            continue
        if s.lstrip().startswith('"""') or s.lstrip().startswith("'''"):
            q = '"""' if '"""' in s else "'''"
            if s.count(q) >= 2 and s.strip() != q:
                i += 1
                continue
            i += 1
            while i < len(lines) and q not in lines[i]:
                i += 1
            if i < len(lines):
                i += 1
            continue
        break
    return "".join(lines[i:])


def fix_usage(text: str, module: str) -> str:
    """Rewrite manim Usage paths to video_project location."""
    text = re.sub(
        r"yty_manim/application/[\w_]+\.py",
        f"video_project/cs2_c4/manim/{module}.py",
        text,
    )
    text = text.replace("MirageShockwaveDemoScene", "MirageShockwaveScene")
    return text


def write(name: str, content: str) -> None:
    path = DEST / name
    path.write_text(content, encoding="utf-8")
    print(f"wrote {path.relative_to(ROOT)} ({len(content.splitlines())} lines)")


def main() -> None:
    DEST.mkdir(parents=True, exist_ok=True)

    # ── titles.py: toc + three title cards ─────────────────────────────
    toc = strip_module_banner(read("toc_contents_demo.py"))
    pf_t = strip_module_banner(read("pathfinding_title_demo.py"))
    sw_t = strip_module_banner(read("shockwave_title_demo.py"))
    pb_t = strip_module_banner(read("prebake_title_demo.py"))

    # Deduplicate: keep one TitleCardResult from pathfinding; rename prebake's
    pb_t = pb_t.replace("class TitleCardResult:", "class PrebakeTitleCardResult:")
    pb_t = pb_t.replace("-> TitleCardResult:", "-> PrebakeTitleCardResult:")
    pb_t = pb_t.replace("return TitleCardResult(", "return PrebakeTitleCardResult(")
    # remove duplicate __all__ / future / imports when concatenating — keep header once
    def drop_top_imports(body: str) -> str:
        body = re.sub(r"^from __future__ import annotations\n+", "", body, count=1, flags=re.M)
        body = re.sub(r"^from dataclasses import dataclass\n+", "", body, count=1, flags=re.M)
        body = re.sub(r"^import numpy as np\n+", "", body, count=1, flags=re.M)
        body = re.sub(r"^from manim import \*\n+", "", body, count=1, flags=re.M)
        body = re.sub(
            r"^from yty_manim\.disposition\.fonts_and_colors import .*\n+",
            "",
            body,
            count=1,
            flags=re.M,
        )
        body = re.sub(r"^__all__ = \([^)]*\)\n+", "", body, count=1, flags=re.M | re.S)
        return body

    titles = fix_usage(
        '''# rainbow_yu — CS2 C4 成片：目录与章节标题卡
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

'''
        + "\n# ── 内容总览 ────────────────────────────────────────────────\n\n"
        + drop_top_imports(toc)
        + "\n# ── 冲击波标题 ──────────────────────────────────────────────\n\n"
        + drop_top_imports(sw_t)
        + "\n# ── 搜索算法标题 ────────────────────────────────────────────\n\n"
        + drop_top_imports(pf_t)
        + "\n# ── 预烘焙标题 ──────────────────────────────────────────────\n\n"
        + drop_top_imports(pb_t),
        "titles",
    )
    # play_prebake return type already fixed; ensure import of gradient only once — ok
    write("titles.py", titles)

    # ── pathfinding.py ────────────────────────────────────────────────
    pf = read("pathfinding_algorithms_demo.py")
    pf = pf.replace(
        "from yty_manim.application.pathfinding_title_demo import play_pathfinding_title_card",
        "from video_project.cs2_c4.manim.titles import play_pathfinding_title_card",
    )
    # Prefer relative import that works when run as manim file — use package path.
    # video_project may not be a package; use importlib-friendly path:
    # Actually `video_project.cs2_c4.manim` needs __init__.py files.
    pf = fix_usage(pf, "pathfinding")
    pf = pf.replace(
        "# rainbow_yu — 2D pathfinding / distance-field algorithm showcase (CS2 C4 extension)",
        "# rainbow_yu — CS2 C4 成片：搜索 / 距离场算法",
    )
    write("pathfinding.py", pf)

    # ── shockwave.py = algorithm + 3d bomb contrast ───────────────────
    sw = strip_module_banner(read("shockwave_algorithm_demo.py"))
    bomb3d = strip_module_banner(read("cs2_bomb_3d_demo.py"))
    bomb3d = drop_top_imports(bomb3d) if False else bomb3d
    # bomb3d starts with from __future__ and imports
    bomb3d_body = drop_top_imports(bomb3d)
    # remove star import of arena from bomb3d_body if present
    bomb3d_body = re.sub(
        r"^from yty_manim\.basic_unit\.cs2_arena import \*  # noqa: F401,F403\n+",
        "",
        bomb3d_body,
        count=1,
        flags=re.M,
    )
    bomb3d_body = re.sub(r"^__all__ = \([^)]*\)\n+", "", bomb3d_body, count=1, flags=re.M | re.S)

    sw_body = drop_top_imports(sw)
    # shockwave already imports from cs2_arena specifically — keep those by not dropping from first file fully
    # Actually drop_top_imports removed manim imports — rebuild header
    shockwave = fix_usage(
        '''# rainbow_yu — CS2 C4 成片：冲击波算法与三维对比
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
from yty_manim.basic_unit.cs2_arena import (
    BOMB_IJ,
    CELL_2D as CELL,
    GRID,
    MAP_SCALE,
    MAP_SHIFT,
    SURVIVOR_IJ,
    FormulaLine,
    GridMap2D,
    _bfs_dist,
    _bfs_path,
    _heat_color,
    _ij_to_xy,
    _layers_from_dist,
    _path_mobject,
)
from yty_manim.basic_unit.cs2_map import WAVE_SPEED_M_S
from yty_manim.disposition.fonts_and_colors import text_font

__all__ = (
    "ShockwaveAlgorithmScene",
    "OldBombSphere3DScene",
    "NewBombSearch3DScene",
)

'''
        + "\n# ── 冲击波算法讲解 ──────────────────────────────────────────\n\n"
        + sw_body
        + "\n# ── 三维球体 vs 路径波 ──────────────────────────────────────\n\n"
        + bomb3d_body,
        "shockwave",
    )
    # Remove duplicate imports left inside sw_body
    shockwave = re.sub(
        r"^from yty_manim\.basic_unit\.cs2_arena import \(\n(?:.*\n)*?\)\n",
        "",
        shockwave,
        count=2,
        flags=re.M,
    )
    shockwave = re.sub(
        r"^from yty_manim\.basic_unit\.cs2_map import WAVE_SPEED_M_S\n",
        "",
        shockwave,
        count=1,
        flags=re.M,
    )
    shockwave = re.sub(
        r"^from yty_manim\.disposition\.fonts_and_colors import text_font\n",
        "",
        shockwave,
        count=1,
        flags=re.M,
    )
    shockwave = re.sub(r"^__all__ = \(\"ShockwaveAlgorithmScene\",\)\n+", "", shockwave, count=1, flags=re.M)
    write("shockwave.py", shockwave)

    # ── prebake.py ────────────────────────────────────────────────────
    pb = read("prebake_algorithm_demo.py")
    pb = pb.replace(
        "from yty_manim.application.prebake_title_demo import play_prebake_title_card",
        "from video_project.cs2_c4.manim.titles import play_prebake_title_card",
    )
    viz = strip_module_banner(read("explosion_prebake_viz.py"))
    viz_body = drop_top_imports(viz)
    viz_body = re.sub(
        r"^from yty_manim\.basic_unit\.cs2_damage import \(\n(?:.*\n)*?\)\n",
        "",
        viz_body,
        count=1,
        flags=re.M,
    )
    viz_body = re.sub(r"^__all__ = \([^)]*\)\n+", "", viz_body, count=1, flags=re.M | re.S)
    # Extract damage imports from viz for header merge — prebake already has many
    # Keep viz as second part; it needs its own imports if missing from prebake
    # Safer: append viz file almost intact after prebake with its imports kept
    viz_keep = strip_module_banner(read("explosion_prebake_viz.py"))
    viz_keep = re.sub(r"^from __future__ import annotations\n+", "", viz_keep, count=1, flags=re.M)
    viz_keep = re.sub(r"^__all__ = \([^)]*\)\n+", "", viz_keep, count=1, flags=re.M | re.S)

    pb = re.sub(
        r'^"""[\s\S]*?"""\n+',
        '"""预烘焙算法整合篇 + 分镜可视化。\\n\\n'
        "Usage:\\n"
        "    python -m manim -qh video_project/cs2_c4/manim/prebake.py PrebakeAlgorithmScene\\n"
        "    python -m manim -qh video_project/cs2_c4/manim/prebake.py ExplosionPrebakeVisualization\\n"
        '"""\n\n',
        pb,
        count=1,
    )
    pb = fix_usage(pb, "prebake")
    pb = pb.replace(
        "# rainbow_yu — 预烘焙算法整合篇（标题卡 + 伤害场教学 + CS2 答卷）",
        "# rainbow_yu — CS2 C4 成片：预烘焙算法",
    )
    # If pb ends without viz, append
    if "class ExplosionPrebakeVisualization" not in pb:
        pb = pb.rstrip() + "\n\n# ── 预烘焙分镜可视化 ────────────────────────────────────────\n\n" + viz_keep
    write("prebake.py", pb)

    # ── damage_field_3d.py ────────────────────────────────────────────
    df = read("explosion_damage_field_3d_demo.py")
    df = fix_usage(df, "damage_field_3d")
    df = df.replace(
        "# rainbow_yu — 3D 爆炸伤害场 · 梯度下降采样点",
        "# rainbow_yu — CS2 C4 成片：三维爆炸伤害场",
    )
    write("damage_field_3d.py", df)

    # ── mirage.py = bomb_wave + map_shockwave ──────────────────────────
    wave = read("cs2_bomb_wave.py")
    wave = wave.replace("MirageShockwaveDemoScene", "MirageShockwaveScene")
    wave = fix_usage(wave, "mirage")
    wave = wave.replace(
        "# rainbow_yu — CS2 C4 shockwave Manim scenes (Mirage real layout + source code linkage)",
        "# rainbow_yu — CS2 C4 成片：Mirage 冲击波与地图 bundle",
    )
    map_sc = strip_module_banner(read("map_shockwave_scene.py"))
    map_sc = re.sub(r"^from __future__ import annotations\n+", "", map_sc, count=1, flags=re.M)
    # avoid duplicate UI helpers — append as section
    if "class CustomMapShockwaveScene" not in wave:
        wave = wave.rstrip() + "\n\n# ── 自定义 MapBundle 冲击波 ─────────────────────────────────\n\n" + map_sc
    # update __all__
    if '"MirageShockwaveScene"' not in wave and "MirageShockwaveScene" in wave:
        wave = wave.replace('"MirageShockwaveDemoScene"', '"MirageShockwaveScene"')
    if "CustomMapShockwaveScene" in wave and '"CustomMapShockwaveScene"' not in wave:
        wave = wave.replace(
            '"OutroScene",\n)',
            '"OutroScene",\n    "CustomMapShockwaveScene",\n    "CustomMapStaticScene",\n)',
        )
    write("mirage.py", wave)

    # package markers so `from video_project.cs2_c4.manim.titles import ...` works
    for pkg in [
        ROOT / "video_project" / "__init__.py",
        ROOT / "video_project" / "cs2_c4" / "__init__.py",
        DEST / "__init__.py",
    ]:
        if not pkg.exists():
            pkg.write_text("# rainbow_yu video_project package\n", encoding="utf-8")
            print("created", pkg.relative_to(ROOT))

    # README for manim folder
    (DEST / "README.md").write_text(
        """# CS2 C4 Manim 成片脚本

可复用单元在 `yty_manim/basic_unit`（`cs2_arena` / `cs2_damage` / `cs2_map`）。  
本目录仅放成片 Scene，输出建议拷到 `../cs2_c4_edit/manim/`。

```bash
# 仓库根目录执行
python -m manim -qh video_project/cs2_c4/manim/titles.py ContentsPageScene
python -m manim -qh video_project/cs2_c4/manim/shockwave.py ShockwaveAlgorithmScene
python -m manim -qh video_project/cs2_c4/manim/pathfinding.py PathfindingAlgorithmsScene
python -m manim -qh video_project/cs2_c4/manim/prebake.py PrebakeAlgorithmScene
python -m manim -qh video_project/cs2_c4/manim/mirage.py MirageShockwaveScene
python -m manim -qh --disable_caching video_project/cs2_c4/manim/damage_field_3d.py ExplosionDamageField3D
```
""",
        encoding="utf-8",
    )

    # Update render_all.bat
    bat = ROOT / "video_project" / "cs2_c4" / "cs2_c4_edit" / "render_all.bat"
    bat.write_text(
        """@echo off
cd /d "%~dp0..\\..\\.."
if not exist "video_project\\cs2_c4\\cs2_c4_edit\\manim" mkdir "video_project\\cs2_c4\\cs2_c4_edit\\manim"
python -m manim -qh -v WARNING --disable_caching video_project/cs2_c4/manim/mirage.py IntroHookScene OldVsNewBombScene PatchTimelineScene SourcePipelineScene GameEvidenceScene ThreePositionScene MapBakeBFSScene RuntimeLookupScene DamagePreviewHUDScene DamageCurveScene MirageShockwaveScene OutroScene
if errorlevel 1 exit /b 1
xcopy /Y /Q "media\\videos\\mirage\\1080p60\\*.mp4" "video_project\\cs2_c4\\cs2_c4_edit\\manim\\"
echo Render complete. Run video_project\\cs2_c4\\cs2_c4_edit\\build_video.ps1 to assemble.
""",
        encoding="utf-8",
    )
    print("updated render_all.bat")

    # Delete application CS2 files
    to_del = [
        "cs2_bomb_3d_demo.py",
        "cs2_bomb_wave.py",
        "cs2_bomb_wave_recovered.py",
        "explosion_damage_field_3d_demo.py",
        "explosion_prebake_viz.py",
        "map_shockwave_scene.py",
        "pathfinding_algorithms_demo.py",
        "pathfinding_title_demo.py",
        "prebake_algorithm_demo.py",
        "prebake_title_demo.py",
        "shockwave_algorithm_demo.py",
        "shockwave_title_demo.py",
        "toc_contents_demo.py",
    ]
    for n in to_del:
        p = APP / n
        if p.exists():
            p.unlink()
            print("del", n)

    print("DONE")


if __name__ == "__main__":
    main()
