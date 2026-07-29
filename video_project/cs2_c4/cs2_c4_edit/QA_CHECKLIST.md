# 成片质检清单

- [x] 总时长 ≥ 6:30（当前拉伸版 **8:00**）
- [x] 12 段 Manim 均在 `cs2_c4_edit/manim/`
- [x] 实机占位素材在 `cs2_c4_footage/raw/`（**请替换为真实录屏**）
- [ ] 旁白 `audio/narration.wav` 本人录制（测试轨：`narration_silent.wav`）
- [x] `build_video.ps1` 输出 `output/cs2_c4_shockwave_final.mp4`
- [x] 字幕与四幕时间轴对齐（`subtitles_zh.srt` · 29 条 / 8:00）
- [ ] 加长版 Manim `-qh` 渲染完成后重新 `build_video.ps1`（后台 `render_all.bat` 进行中）
- [ ] cl_bake_bomb_damage_debug 命令可读（需真实 debug 录屏）
- [ ] 【推断】段有角标或语气区分（字幕已标注，配音待录）

## 一键流程

```powershell
cd video_project/cs2_c4/cs2_c4_edit
.\render_all.bat          # Manim 1080p60（加长 Scene）
.\build_video.ps1         # 拉伸对齐 + 拼接 + 字幕
.\compose_video.ps1       # 可选 PiP 进阶合成
```

## 你还需要做的

1. 按 `cs2_c4_footage/README_RECORDING.md` 录制 4 条真实 CS2 素材，覆盖 `raw/`
2. 按 `audio/RECORD_NARRATION.md` 录制 `narration.wav`，再跑 `build_video.ps1`
3. `render_all.bat` 跑完后，用新 `manim/*.mp4` 重新导出（画面会更长，可能减少定格拉伸）
