# 旁白与 BGM 混音说明

## 旁白文件

- 路径：`cs2_c4_edit/audio/narration.wav`
- 格式：48kHz，mono，16-bit PCM
- 录音稿：`NARRATION_zh.md`（11 镜）

## BGM 建议（四幕）

| 时段 | 镜号 | 风格 | 音量（相对旁白） |
|------|------|------|------------------|
| 0:00–2:20 | 01–03b | 低鼓点 / 紧张铺垫 | -18 dB |
| 2:20–3:55 | 04–05 | 环境电子 | -20 dB |
| 3:55–6:35 | 06–09 | 极简钢琴或静音 | -24 dB 或无 |
| 6:35–8:00 | 10–11 | 渐强后淡出 | -15 dB → fade out |

## 混音命令（旁白已录好后）

```powershell
cd video_project/cs2_c4/cs2_c4_edit
# 假设 BGM 为 audio/bgm.mp3，循环至片长
ffmpeg -y -i output/cs2_c4_shockwave_draft.mp4 -i audio/narration.wav -i audio/bgm.mp3 `
  -filter_complex "[2:a]volume=0.15[bg];[1:a][bg]amix=inputs=2:duration=first[aout]" `
  -map 0:v -map "[aout]" -c:v copy -c:a aac -b:a 192k output/cs2_c4_with_audio.mp4
```

## 占位静音轨（测试管线）

```powershell
ffmpeg -y -f lavfi -i anullsrc=r=48000:cl=mono -t 420 audio/narration_silent.wav
```
