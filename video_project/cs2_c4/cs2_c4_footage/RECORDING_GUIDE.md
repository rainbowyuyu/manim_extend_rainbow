# Mirage C4 冲击波实机素材录制指南

## 前置条件

1. 将配置文件复制到：
   `D:\stream\steamapps\common\Counter-Strike Global Offensive\game\csgo\cfg\`
   - 基础版：[`record_mirage_bomb.cfg`](record_mirage_bomb.cfg)（debug / 证据向）
   - **电影感爆炸**：[`record_explosion_cinematic.cfg`](record_explosion_cinematic.cfg)（慢动作 / 隐 HUD / 第三人称，见 [`EXPLOSION_CINEMATIC_GUIDE.md`](EXPLOSION_CINEMATIC_GUIDE.md)）
2. 启动 CS2，控制台输入：
   ```
   map de_mirage
   exec record_mirage_bomb
   ```
3. 使用 OBS / GeForce Experience / CS2 内置 demo 工具录制 1920×1080 60fps。

## 站位坐标参考（Mirage A 点下包场景）

| 编号 | 站位 | 说明 | 输出文件 |
|------|------|------|----------|
| R1 | A 包点中心偏上 | 开启 debug overlay 后环视地面热力图 | `mirage_a_debug_wide.mp4` |
| R2 | 链接通道（Connector） | 下包后移动至此，录血条闪烁预览 | `mirage_link_preview.mp4` |
| R3 | Jungle 外 / 拐角后 | 展示厚墙阻断或低伤害存活 | `mirage_jungle_survive.mp4` |
| R4 | A 包点内 | 完整爆炸冲击波视觉效果 | `mirage_a_explosion_wave.mp4` |
| R5 | B 包点（可选） | 控制台 `cl_bake_bomb_damage_debug 2` | `mirage_b_debug.mp4` |

## 控制台快捷切换

```
cl_bake_bomb_damage_debug 1   // A 点伤害场
cl_bake_bomb_damage_debug 2   // B 点伤害场
cl_bake_bomb_damage_debug 0   // 关闭 overlay
```

## 血条预览录制技巧

- 下包后不要移动，观察爆炸前 1–2 秒血条红/黄分段闪烁
- 可对比三站位：包点内（必死）、链接（部分伤害）、拐角后（0 或低伤）

## 输出目录

将录制文件放入：

```
video_project/cs2_c4_footage/raw/
```

剪辑脚本 [`../cs2_c4_edit/build_video.ps1`](../cs2_c4_edit/build_video.ps1) 会从此目录读取素材。
