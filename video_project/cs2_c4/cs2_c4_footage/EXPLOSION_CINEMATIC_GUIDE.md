# C4 爆炸 · 电影感录屏指南

## 安装

复制到 CS2 配置目录：

```
Counter-Strike Global Offensive/game/csgo/cfg/record_explosion_cinematic.cfg
```

控制台：

```
map de_mirage
exec record_explosion_cinematic
```

## 与基础 cfg 的区别

| 项目 | `record_mirage_bomb.cfg` | `record_explosion_cinematic.cfg` |
|------|--------------------------|----------------------------------|
| 用途 | 算法片实机证据 / debug 热力 | **爆炸视觉冲击**、B-roll |
| HUD | 默认开启 | `F5` / `F6` 一键隐藏 |
| 慢动作 | 无 | `F7` 35% · `F8` 15% |
| 镜头 | 第一人称 | `F10` 第三人称 · `F11` noclip |
| 后期 | 默认 | Bloom + 略提亮 tonemap |

## 推荐镜头

1. **冲击波走廊**：A 点下包 → 链接 / 中路方向低机位，`cine_slow` + 第一人称或第三人称
2. **环视火球**：`cine_cam_tp` + `cine_ultraslow`，`cine_debug_off` 关掉地面热力
3. **debug 对比**：`cine_debug_a` 开热力 → 切 `cine_debug_off` 再录一版同机位

## OBS 建议

- 1920×1080 · 60fps · CQP/CRF 18 或更高码率
- 爆炸瞬间音量留 -6dB 余量，避免削波
- 慢动作用游戏内 `host_timescale`，比后期 50% 更自然

## 录完

覆盖 `cs2_c4_footage/raw/mirage_a_explosion_wave.mp4`，再跑 `cs2_c4_edit/build_video.ps1`。
