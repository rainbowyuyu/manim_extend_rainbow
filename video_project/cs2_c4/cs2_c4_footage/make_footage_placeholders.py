# 生成实机占位素材（无 CS2 录屏时用于测试剪辑管线）
from __future__ import annotations

import subprocess
from pathlib import Path

RAW = Path(__file__).resolve().parent / "raw"
RAW.mkdir(parents=True, exist_ok=True)

CLIPS = (
    ("mirage_a_explosion_wave.mp4", 12),
    ("mirage_a_debug_wide.mp4", 20),
    ("mirage_link_preview.mp4", 15),
    ("mirage_jungle_survive.mp4", 12),
    ("mirage_b_debug.mp4", 10),
)


def make_clip(name: str, duration: int) -> None:
    out = RAW / name
    if out.exists():
        print("skip", name)
        return
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", f"color=c=0x1a1a1e:s=1920x1080:d={duration}:r=30",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-t", str(duration),
        str(out),
    ]
    subprocess.run(cmd, check=True)
    print("wrote", out)


if __name__ == "__main__":
    for name, dur in CLIPS:
        make_clip(name, dur)
