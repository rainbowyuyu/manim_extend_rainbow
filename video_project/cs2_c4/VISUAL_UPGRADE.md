# CS2 C4 Manim 可视化升级说明

## 新增模块

| 文件 | 作用 |
|------|------|
| [`yty_manim/basic_unit/cs2_map.py`](../../yty_manim/basic_unit/cs2_map.py) | Mirage 数据 / 矢量地图 / 引擎文案常量 |
| [`yty_manim/basic_unit/cs2_arena.py`](../../yty_manim/basic_unit/cs2_arena.py) | 玩具竞技场 + 寻路网格 |
| [`yty_manim/basic_unit/cs2_damage.py`](../../yty_manim/basic_unit/cs2_damage.py) | 预烘焙伤害组件 + 三维伤害丘 |
| [`video_project/cs2_c4/manim/mirage.py`](manim/mirage.py) | Mirage 冲击波成片 Scene（多镜） |
| [`video_project/cs2_c4/manim/`](manim/) | 其余成片：titles / shockwave / pathfinding / prebake / damage_field_3d |

## 真实数据来源

- **编译管线**：`game/csgo_core/gameinfo.gi` → `"cs2_bomb_damage" "1"`
- **烘焙资源**：`maps/de_mirage/baked_bomb_damage.vdata`
- **调试命令**：`cl_bake_bomb_damage_debug 1`
- **UI 字符串**：`settings_damage_prediction`

## 场景亮点

1. **IntroHookScene** — Mirage 全图热力波扩散（`always_redraw` + `smooth`）
2. **OldVsNewBombScene** — 左球体穿墙 vs 右 Mirage 真实路径波
3. **SourcePipelineScene** — `gameinfo.gi` 代码块 → 箭头 → `.vdata` 资源
4. **MapBakeBFSScene** — Dijkstra 烘焙 + 代码高亮 + 发光波前环
5. **RuntimeLookupScene** — 波前数值追踪 + Connector 扣血联动
6. **ThreePositionScene** — A / 链接 / Jungle 三点位实测强度卡片

## 渲染

```bat
cd video_project\cs2_c4\cs2_c4_edit
render_all.bat
build_video.ps1
```

## 实机替换

将录制 MP4 放入 `cs2_c4_footage/raw/` 后重新 `build_video.ps1`。
