# CS2 C4 冲击波机制 · 算法讲解视频分镜脚本

> **项目**：`manim_extend_rainbow` / `video_project/cs2_c4`  
> **目标时长**：≥ 5 分钟（建议成片 **6:00–6:30**）  
> **形式**：Manim 原理动画 + CS2 实机录屏穿插  
> **案例地图**：`de_mirage`（Mirage / 米垃圾）  
> **游戏目录**：`D:\stream\steamapps\common\Counter-Strike Global Offensive`

---

## 一、更新背景（网页调研摘要）

### 1.1 官方更新节点

| 日期 | 版本 | 核心变化 |
|------|------|----------|
| **2026-07-08** | Premier Season 5 | C4 伤害系统全面重做：冲击波传播、地图烘焙数据、血条伤害预览 |
| **2026-07-10** | 热修复 | 移除全图最低 1 点伤害；修复地图区域边界计算；增强掉落武器受力 |

**参考来源**（可放片尾引用）：

- [Dust2.us — July 8 更新](https://www.dust2.us/news/75797/cs2-july-8th-update-brings-bomb-explosion-re-design-new-armory-items)
- [HLTV — Bomb explosion overhauled](https://www.hltv.org/news/45087/bomb-explosion-overhauled-in-new-update)
- [Dot Esports — Season 5 Patch Notes](https://dotesports.com/counter-strike/news/cs2-season-5-update-patch-notes)
- [PCGamesN — 新爆炸机制解读](https://www.pcgamesn.com/counter-strike-2/update-season-5)
- [SkinSniper 伤害场工具](https://skinsniper.com/tools/bomb-damage-radius)（社区标定，非官方）

### 1.2 机制变化（官方表述 + 社区验证）

**旧机制（Season 5 之前）【推断·基于旧版行为】**

- 爆炸伤害近似按**直线距离**结算，存在穿墙满伤等不合理情况。
- 玩家凭经验判断「离包点多远能活」，职业赛场也偶有误判。

**新机制（Season 5）【官方】**

1. **冲击波传播**：爆炸不再瞬间全图结算，而是从包点向外快速扩展的波前。
2. **地图烘焙**：每张官方爆破图在编译时预计算模拟结果，写入 `baked_bomb_damage` 资源。
3. **几何阻挡**：墙体几乎完全阻断；拐角大幅衰减；可走区路径决定伤害。
4. **到达结算**：波前到达玩家位置时才应用该点的烘焙伤害值。
5. **血条预览**：爆炸前短暂显示预计剩余 HP（读同一张烘焙表）。
6. **护甲无效**：炸弹伤害不受护甲减免【社区实测】。

**7 月 10 日热修复补充【官方】**

- 取消「全图至少 1 点伤害」的错误逻辑。
- 修复地图分区边界附近的错误查表。

---

## 二、本地游戏文件与「源代码」定位

> Valve **不公开** C4 冲击波的 C++/VScript 可读源码；可验证的是**编译管线注册**、**地图烘焙资源**、**控制台调试接口**与**音效/本地化字符串**。

### 2.1 已在本机验证的路径

| 类型 | 路径 | 说明 |
|------|------|------|
| **编译管线注册** | `game\csgo_core\gameinfo.gi` L315–318 | `GameSpecificPostMapBuildSteps` → `"cs2_bomb_damage" "1"` |
| **地图烘焙数据** | `game\csgo\maps\de_mirage.vpk` 内 | 资源名：`maps/de_mirage/baked_bomb_damage.vdata` |
| **调试控制台** | 游戏内 ConVar | `cl_bake_bomb_damage_debug 1`（A 点）/ `2`（B 点）/ `0`（关） |
| **录制配置** | `game\csgo\cfg\record_mirage_bomb.cfg` | 本项目已写入，一键 `exec record_mirage_bomb` |
| **包点贴花材质** | VPK 内 `materials/decals/bombsite_*.vmat` | 与 A/B 包点区域标记相关 |
| **伤害字段名** | VPK 字符串扫描 | `_damage_power`、`baked_bomb_damage`、`bombsite` |

### 2.2 含烘焙数据的 11 张爆破图

`de_ancient`, `de_ancient_night`, `de_anubis`, `de_cache`, `de_dust2`, `de_inferno`, `de_mirage`, `de_nuke`, `de_overpass`, `de_train`, `de_vertigo`

（扫描结果见 `video_project/cs2_c4/cs2_c4_data/baked_bomb_damage_scan.json`）

### 2.3 运行时逻辑（推断伪代码，用于 Manim 展示）

> 标注 **【推断】**，与官方行为一致，非反编译原文。

**编译期（`cs2_bomb_damage` 后处理）【推断】**

```cpp
// gameinfo.gi → GameSpecificPostMapBuildSteps → cs2_bomb_damage
for each walkable cell c on nav_mesh:
    dist[c] = WavePropagation(bombsite, c);  // BFS/Dijkstra，不穿墙
    field[c].arrival      = dist[c] / WAVE_SPEED;
    field[c].damage_power = Falloff(dist[c], corners);
Save("maps/<map>/baked_bomb_damage.vdata");
```

**比赛时（每帧）【推断】**

```cpp
float wave_front = detonate_time + (t - t0) * WAVE_SPEED;
float arrival    = baked[pos.site][pos.cell].arrival;
float power      = baked[pos.site][pos.cell].damage_power;

if (wave_front >= arrival)
    ApplyDamage(player, power);   // 护甲不参与

// 爆炸前 UI 预览
preview_hp = player.health - power;
```

**传播速度标定【社区推断】**：`WAVE_SPEED ≈ 27.5 m/s`（与致命区 33–77 m 波程、0.4–1.0 s 到达时间吻合）

### 2.4 如何用 Source2Viewer 自行查看烘焙资源

1. 打开 [Source2Viewer](https://s2v.app/) 或本地 VRF 工具  
2. 加载 `D:\stream\...\game\csgo\maps\de_mirage.vpk`  
3. 搜索 `baked_bomb_damage` → 导出 `.vdata` 原始字节  
4. 用项目脚本栅格化：`python video_project/cs2_c4/cs2_c4_data/parse_baked_bomb_damage.py`

---

## 三、成片结构总览

| 段落 | 镜号 | 时长 | 画面来源 | Manim Scene |
|------|------|------|----------|-------------|
| 钩子 | 01 | 0:25 | 实机爆炸 + 标题 | `IntroHookScene` |
| 对比 | 02 | 0:35 | Manim 左右对比 | `OldVsNewBombScene` |
| 补丁 | 03 | 0:40 | Manim 时间线 | `PatchTimelineScene` |
| 源码证据 | 03b | 0:30 | Manim 管线图 + gameinfo 摘录 | `SourcePipelineScene` |
| 实机 debug | 04 | 0:45 | **录屏** debug overlay | `GameEvidenceScene` |
| 三站位 | 05 | 0:45 | **录屏** + Manim 雷达 | `ThreePositionScene` |
| 算法·烘焙 | 06 | 0:50 | Manim BFS 扩散 | `MapBakeBFSScene` |
| 算法·运行时 | 07 | 0:45 | Manim 查表动画 | `RuntimeLookupScene` |
| 算法·预览 | 08 | 0:30 | Manim HUD + **录屏血条** | `DamagePreviewHUDScene` |
| 数值曲线 | 09 | 0:30 | Manim 曲线图 | `DamageCurveScene` |
| 综合演示 | 10 | 1:00 | Manim Mirage 矢量冲击波 | `MirageShockwaveDemoScene` |
| 收尾 | 11 | 0:20 | 实机 + 金句 | `OutroScene` |
| **合计** | | **~6:20** | | |

---

## 四、逐镜分镜表

### 镜 01 · 钩子 —「一颗炸弹改了竞技 CS」

| 项 | 内容 |
|----|------|
| **时长** | 0:00 – 0:25（25s） |
| **画面** | 实机：Mirage A 点 C4 爆炸，冲击波沿走廊蔓延（`mirage_a_explosion_wave.mp4`）；叠字标题 |
| **Manim** | `IntroHookScene`：暗场 → 橙红冲击波环快速扩张 → 标题「CS2 C4 冲击波 · 背后的算法」 |
| **旁白** | 2026 年 7 月，Valve 在 Premier Season 5 改了游戏里最重要的一颗炸弹。以前伤害常按直线距离甚至穿墙结算；现在你会看到一股冲击波从包点沿地图蔓延。今天以 Mirage 为例，拆解背后的计算机算法。 |
| **字幕关键词** | Season 5 · 冲击波 · Mirage |
| **音效** | 实机 C4 爆炸音（游戏内 `C4Shockwave` 音效轨，若录屏已含则直接用） |

---

### 镜 02 · 旧 vs 新 —「半径球 → 路径波」

| 项 | 内容 |
|----|------|
| **时长** | 0:25 – 1:00（35s） |
| **画面** | Manim 分屏：左「旧」球形伤害区穿墙；右「新」波沿可走区传播、遇墙断开 |
| **Manim** | `OldVsNewBombScene` |
| **算法点** | 从 **欧氏距离模型** 切换到 **图上的最短路径 / 波前传播模型** |
| **旁白** | 左边是旧思路：以炸弹为圆心画一个球，墙另一边的人照样吃满伤害。右边是新思路：波沿着可走区域传播，遇墙断开，绕到拐角后面伤害大幅衰减甚至为零。关键变化：决定生死的不再是直线距离，而是冲击波沿地图走到你脚下的那条路径。 |
| **可视化要素** | 虚线直线距离 vs 橙色路径高亮；墙块标红「阻断」 |

---

### 镜 03 · 官方补丁时间线

| 项 | 内容 |
|----|------|
| **时长** | 1:00 – 1:40（40s） |
| **画面** | Manim 时间轴：7/8 主更新 → 7/10 热修复 |
| **Manim** | `PatchTimelineScene` |
| **旁白** | 7 月 8 日主更新做了三件事：伤害预计算并烘焙进每张图；冲击波外扩但到达才结算；爆炸前血条闪烁预览。7 月 10 日热修复移除了全图最低 1 点伤害的 bug，并修复地图边界查表问题。 |
| **屏幕文字** | 三条 bullet + 热修复两条 |

---

### 镜 03b · 源码证据 — 编译管线

| 项 | 内容 |
|----|------|
| **时长** | 1:40 – 2:10（30s） |
| **画面** | Manim 流程图：Hammer 地图 → Resource Compiler → Nav → **`cs2_bomb_damage`** → `de_mirage.vpk` |
| **Manim** | `SourcePipelineScene` |
| **实机辅助** | 可闪切 1 秒：记事本打开 `gameinfo.gi` 高亮第 317 行（需录屏或截图） |
| **旁白** | 编译管线在 gameinfo.gi 里注册了后处理步骤 cs2_bomb_damage——和烘焙光照、导航网格一样，是地图编译流程的一部分。产物写进 de_mirage.vpk，资源名叫 baked_bomb_damage。 |
| **屏幕代码** | 见 `yty_manim/basic_unit/cs2_map.py` → `GAMEINFO_BOMB_PIPELINE` |

```gi
GameSpecificPostMapBuildSteps
{
    "cs2_bomb_damage"      "1"
}
```

---

### 镜 04 · 实机证据 — debug 伤害场

| 项 | 内容 |
|----|------|
| **时长** | 2:10 – 2:55（45s） |
| **画面** | **录屏**：`map de_mirage` → `exec record_mirage_bomb` → 地面彩色伤害场 |
| **Manim 兜底** | `GameEvidenceScene`（无录屏时用） |
| **操作清单** | 控制台输入 `cl_bake_bomb_damage_debug 1`；环视 A 点地面热力 |
| **旁白** | 在本地服打开控制台，输入 cl_bake_bomb_damage_debug 1，Mirage A 点地面会显示伤害场。你看到的颜色不是实时算出来的特效，而是编译地图时写进 vpk 的数据。 |
| **输出文件** | `cs2_c4_footage/raw/mirage_a_debug_wide.mp4` |
| **后期** | 画中画叠加 Manim 小雷达同步高亮 |

---

### 镜 05 · 三站位对比 — 同包不同命

| 项 | 内容 |
|----|------|
| **时长** | 2:55 – 3:40（45s） |
| **画面** | 三分屏或顺序切换：A 包点内 / 链接 / Jungle 拐角 |
| **录屏** | `mirage_link_preview.mp4`、`mirage_jungle_survive.mp4` |
| **Manim** | `ThreePositionScene`：Mirage 雷达三点标注 + 伤害数值 |
| **旁白** | 同一张 Mirage，A 点下包，三个位置结果完全不同：包点内满血必死；链接通道波沿走廊传来，血条提前告诉你还剩多少 HP；Jungle 拐角后厚墙阻断，可能零伤害存活。护甲对炸弹无效，买甲是为了对枪，不是为了抗 C4。 |
| **数据标注** | 链接 ~数十米级伤害；Jungle 0 HP |

---

### 镜 06 · 算法① — 离线烘焙（BFS / 波前传播）

| 项 | 内容 |
|----|------|
| **时长** | 3:40 – 4:30（50s） |
| **画面** | Manim：Mirage 俯视栅格，从 A 点逐层 BFS 染色扩散；遇墙停止；拐角格衰减 |
| **Manim** | `MapBakeBFSScene` |
| **算法讲解** | **广度优先搜索（BFS）** 或带权 **Dijkstra**：在可走区图上游走，记录每个格点的 `dist` 与 `damage_power` |
| **旁白** | 编译地图时可以这样理解：从 A 点出发，在可行走区域做广度优先搜索，一层层向外扩展。每走一步记录波到达的距离和剩余强度。穿墙不可达；绕角代价更高，强度衰减。全部格点算完后写入 baked_bomb_damage。这是一次性离线计算，比赛时零延迟查表。 |
| **屏幕公式** | `arrival[c] = dist[c] / WAVE_SPEED` |
| **对比工业界** | 游戏寻路、网络路由、洪水填充（Flood Fill）同属图传播问题 |

---

### 镜 07 · 算法② — 运行时 O(1) 查表

| 项 | 内容 |
|----|------|
| **时长** | 4:30 – 5:15（45s） |
| **画面** | Manim：时间轴上 `wave_front` 线向右移动；玩家脚下格子高亮；满足条件时扣血 |
| **Manim** | `RuntimeLookupScene` |
| **核心代码（屏显）** | 四步面板（见 `RUNTIME_CODE_STEPS`） |
| **旁白** | 比赛时不再重新模拟整张地图。逻辑可以简化为：如果冲击波前沿已经到达或超过你位置的波达时间，就按烘焙表扣血。视觉上的圆环在向外扩，但数学上每个玩家的伤害早就在表里写好了——O(1) 查表，不是 O(地图) 实时模拟。 |
| **强调** | **预计算换性能** |

---

### 镜 08 · 算法③ — 血条预测

| 项 | 内容 |
|----|------|
| **时长** | 5:15 – 5:45（30s） |
| **画面** | Manim：HUD 血条 + 公式；穿插 3 秒录屏血条闪烁 |
| **Manim** | `DamagePreviewHUDScene` |
| **公式** | `preview_hp = current_hp - baked_damage[pos]` |
| **旁白** | 血条预览并不神秘：爆炸前读同一张表，所以预览和最终结算一致——前提是爆炸前你没有换位置。 |
| **注意** | 区分「客户端伤害预测 settings_damage_prediction」（射击手感）与「炸弹 HP 预览」（烘焙表）——后者是 C4 专用机制 |

---

### 镜 09 · 数值直觉 — 伤害曲线

| 项 | 内容 |
|----|------|
| **时长** | 5:45 – 6:15（30s） |
| **画面** | Manim：强度→HP 曲线；标注 20%≈33HP、40%≈77HP、>100 致死 |
| **Manim** | `DamageCurveScene` |
| **数据来源** | SkinSniper 社区标定 + 本项目 `mirage_baked_site_a.npz` 交叉验证 |
| **旁白** | 社区用地图原始数据标定过近似曲线：20% 强度约 33 HP，40% 约 77 HP，超过 100 即致死。Mirage A 点大约在波传播 33 到 77 米内伤害仍超过 100。 |

---

### 镜 10 · 综合演示 — Mirage 矢量冲击波（高潮）

| 项 | 内容 |
|----|------|
| **时长** | 6:15 – 7:15（60s） |
| **画面** | Manim：`MirageVectorMap` 矢量地图 + 流体等高线波前；右侧代码步骤逐条高亮；站位采样 HUD |
| **Manim** | `MirageShockwaveScene` |
| **算法可视化** | 2× 上采样距离场 + 等高线波前；格点热力层；Dijkstra 路径距离 |
| **旁白** | 波从 A 点出发，沿可走区扩散到链接、Jungle、CT 家——每个位置的到达时间与伤害，都来自 baked_bomb_damage。右侧是运行时查表的四步逻辑。 |
| **渲染命令** | `python -m manim -qh video_project/cs2_c4/manim/mirage.py MirageShockwaveScene` |

---

### 镜 11 · 收尾

| 项 | 内容 |
|----|------|
| **时长** | 7:15 – 7:35（20s） |
| **画面** | 实机爆炸慢镜头或静态雷达；片尾引用链接 |
| **Manim** | `OutroScene` |
| **旁白** | CS2 用预计算换性能，用路径换公平——隔墙死、背半径的时代过去了。保枪决策从「离炸弹多远」，变成了「冲击波怎么绕地图找到你」。算法就藏在 maps/de_mirage.vpk 的 baked_bomb_damage 里。 |
| **片尾字卡** | 参考资料 + `cl_bake_bomb_damage_debug 1` 试玩提示 |

---

## 五、实机录屏清单

录屏前执行：

```
map de_mirage
exec record_mirage_bomb
```

| 文件 | 镜号 | 内容 | 时长建议 |
|------|------|------|----------|
| `mirage_a_explosion_wave.mp4` | 01, 11 | A 点真实爆炸冲击波 | 8–15s |
| `mirage_a_debug_wide.mp4` | 04 | debug 地面伤害场环视 | 15–25s |
| `mirage_link_preview.mp4` | 05, 08 | 链接站位 + 血条预览 | 10–20s |
| `mirage_jungle_survive.mp4` | 05 | Jungle 拐角存活 | 10–15s |
| `mirage_b_debug.mp4` | 可选 | B 点伤害场 | 10s |

存放路径：`video_project/cs2_c4_footage/raw/`

详细步骤见 `cs2_c4_footage/RECORDING_GUIDE.md`

---

## 六、Manim 渲染清单

在项目根目录执行（可先 `-ql` 预览，成片 `-qh`）：

```bash
python -m manim -qh -v WARNING video_project/cs2_c4/manim/mirage.py ^
  IntroHookScene OldVsNewBombScene PatchTimelineScene SourcePipelineScene ^
  GameEvidenceScene ThreePositionScene MapBakeBFSScene RuntimeLookupScene ^
  DamagePreviewHUDScene DamageCurveScene MirageShockwaveScene OutroScene
```

或一键：`video_project/cs2_c4/cs2_c4_edit/render_all.bat`

输出目录：`video_project/cs2_c4/cs2_c4_edit/manim/`

---

## 七、剪辑合成

```powershell
cd video_project/cs2_c4/cs2_c4_edit
.\build_video.ps1
```

脚本按本分镜顺序拼接实机 + Manim，并烧录 `subtitles_zh.srt`（若有）。

---

## 八、旁白全文

完整中文旁白稿（可直接录音）见：

`video_project/cs2_c4/cs2_c4_edit/NARRATION_zh.md`

语速建议 **180–200 字/分钟**，全稿约 **6 分 10 秒**。

---

## 九、事实标注规范（成片角标建议）

| 标注 | 含义 | 示例 |
|------|------|------|
| **【官方】** | Valve 补丁/本地化/本地 gameinfo 可证实 | 烘焙机制、血条预览、热修复 |
| **【实测】** | 本机 debug / 录屏 / SkinSniper 交叉 | 护甲无效、Mirage 三站位 |
| **【推断】** | 合理技术推断，非反编译原文 | BFS 烘焙、WAVE_SPEED=27.5、运行时伪代码 |

---

## 十、制作排期建议

| 阶段 | 任务 | 预估 |
|------|------|------|
| D1 | 实机录屏 5 条 + 提取 `baked_bomb_damage` | 2h |
| D2 | Manim 全场景 `-ql` 预览迭代 | 3h |
| D3 | 旁白录音 + 字幕 | 2h |
| D4 | Manim `-qh` 最终渲染 | 4h（可挂机） |
| D5 | `build_video.ps1` 合成 + 调色 + 导出 | 2h |

---

## 十一、核心算法一句话总结（片内金句）

> **编译时用图传播算法把「冲击波会怎么绕地图找到你」算一遍写进文件；比赛时只做波前推进 + 查表。**

---

*文档版本：2026-07-12 · 对应 CS2 Premier Season 5（2026-07-08）及 07-10 热修复*
