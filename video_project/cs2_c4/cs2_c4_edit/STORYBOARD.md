# CS2 C4 冲击波视频 — 分镜剪辑表

| 镜号 | 时间轴 | 素材文件 | 类型 |
|------|--------|----------|------|
| 01 | 0:00–0:41 | IntroHookScene.mp4 或 mirage_a_explosion_wave.mp4 | 实机/Manim |
| 02 | 0:41–0:59 | OldVsNewBombScene.mp4 | Manim |
| 03 | 0:59–1:25 | PatchTimelineScene.mp4 | Manim |
| 04 | 1:25–2:08 | GameEvidencePlaceholderScene.mp4 或 mirage_a_debug_wide.mp4 | 实机/Manim |
| 05 | 2:08–2:50 | ThreePositionPlaceholderScene.mp4 或 mirage_link_preview.mp4 | 实机/Manim |
| 06 | 2:50–3:25 | MapBakeBFSScene.mp4 | Manim |
| 07 | 3:25–3:51 | RuntimeLookupScene.mp4 | Manim |
| 08 | 3:51–4:17 | DamagePreviewHUDScene.mp4 | Manim |
| 09 | 4:17–4:45 | DamageCurveScene.mp4 | Manim |
| 10 | 4:45–5:22 | OutroScene.mp4 或 mirage_a_explosion_wave.mp4 | 实机/Manim |

**当前合成时长（Manim 占位版）**：约 **5:22**（322 秒）

## 合成命令

```powershell
cd video_project\cs2_c4_edit
.\build_video.ps1
```

输出：`output/cs2_c4_shockwave_final.mp4`

## 替换实机素材

将录制文件放入 `cs2_c4_footage/raw/` 后重新运行 `build_video.ps1`，脚本会自动优先使用实机片段。
