# CS / Map / 爆炸 — 二次合并（对齐 squ_tex 习惯）

日期: 2026-07-30

## 最终结构（3 个 basic_unit 模块）

```
yty_manim/basic_unit/
  cs2_arena.py    # GRID / Arena3D / GridMap2D / 寻路算法
  cs2_damage.py   # 预烘焙组件 / DamageHill3D / intensity_color
  cs2_map.py      # Mirage 数据+渲染 / MapBundle 视图 / 引擎文案
```

`application/` 仅保留 Scene 编排；已删除碎片 shim。

## 书写习惯

- 头注释：`# rainbow_yu manim_extend.basic_unit.xxx 🐋✨`
- 顶部 `__all__`
- 公开类：中文 Notes / Examples，继承 `VGroup` / `Group`
