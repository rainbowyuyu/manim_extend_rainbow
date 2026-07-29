# 实机录屏说明

## 已就绪

- CS2 配置已部署：`game/csgo/cfg/record_mirage_bomb.cfg`
- 占位素材已生成：`raw/*.mp4`（**请用真实录屏替换**）

## 录制步骤

```
map de_mirage
exec record_mirage_bomb
```

| 文件 | 内容 |
|------|------|
| `mirage_a_debug_wide.mp4` | A 点 debug 环视 20s |
| `mirage_link_preview.mp4` | 链接站位 + 血条预览 15s |
| `mirage_jungle_survive.mp4` | Jungle 拐角存活 12s |
| `mirage_a_explosion_wave.mp4` | A 点冲击波 12s |

输出目录：`cs2_c4_footage/raw/`（覆盖占位文件即可）

详细站位见 [`RECORDING_GUIDE.md`](RECORDING_GUIDE.md)
