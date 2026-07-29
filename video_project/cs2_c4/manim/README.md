# CS2 C4 Manim 成片脚本

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
