# CS2 风格爆炸伤害预烘焙 · 教学动画设计说明

## 一、动画设计概述

本片用 **教学简化模型**（非 Valve 实装）解释：为何要预估爆炸伤害、如何离散化地图、如何烘焙空间伤害场、如何处理距离衰减与墙体材质遮挡、运行时如何采样，以及如何把预计伤害映射到血条红色预览区。

视觉：深色背景、抽象俯视地图、橙红爆心、点阵热力伤害场、圆点玩家、绿血条 + 半透明红预览。公式用 ASCII（本机无 LaTeX），并与地图对象联动。

节奏：**问题 → 直觉 → 数学模型 → 计算演示 → 工程优化 → 完整管线**。  
正式片 `CFG_FAST=False`：动画正常速、读图停顿拉长，目标约 **8～10 分钟**。

---

## 二、分镜表（摘要）

| 场景 | 画面 | 动作 | 核心公式 | 教学目标 |
|------|------|------|----------|----------|
| 1 | HUD + 三方案 | 射线拥挤 / 热力 / 采样 | — | 引出预烘焙+采样 |
| 2 | 地图/墙/三玩家 | 脉冲环 | e | 建立空间语言 |
| 3 | 距离线+直角边 | 勾股展开 | d=√… | 欧氏距离 |
| 4 | 半径+衰减曲线 | 线性→二次 | (1-u)² | 衰减与 clamp |
| 5 | 点阵逐圈上色 | 单格→全场 | D_ij | 伤害场 |
| 6 | 三射线遮挡 | V=1/部分/0 | D·V | 近≠高伤 |
| 7 | 距离场→遮挡场 | 原地改写 | +visibility | 非圆对称 |
| 8 | 路径+曲线 | NN/双线性 | 双线性 | 运行时查表 |
| 9 | 放大血条 | 红区/致死 | H_after | HUD 预览 |
| 10 | 流程图 | 脏区 | — | 缓存失效 |
| 11 | 左右复杂度 | O 示意 | O(FPK) vs O(P) | 效率 |
| 12 | 三档精度卡 | 权衡 | — | 误差换效率 |
| 13 | 九步管线 | 金句 | H_preview | 复盘 |

---

## 三、算法要点

`D(p) = D_max * (1-u)^2 * V(e,p)`，`u=clamp(d/R,0,1)`。  
网格烘焙 → 最近邻/双线性采样 → `H_after = max(0, H - A*D_sample)`。

---

## 四～七、代码与命令

- 核心：`yty_manim/application/explosion_prebake_core.py`
- 场景：`yty_manim/application/explosion_prebake_viz.py`

```bash
python -m manim -qh yty_manim/application/explosion_prebake_viz.py ExplosionPrebakeVisualization
python -m manim -pql yty_manim/application/explosion_prebake_viz.py ExplosionPrebakeVisualization
```

试渲设 `CFG_FAST = True`。成片建议拷到 `video_project/cs2_c4/cs2_c4_edit/manim/explosion_prebake.mp4`。
