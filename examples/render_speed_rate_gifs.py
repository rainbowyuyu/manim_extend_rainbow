# -*- coding: utf-8 -*-
"""批量渲染 speed_rate_fuc 示例 GIF，并整理到 yty_manim/examples/speed_rate/。"""

from __future__ import annotations

import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
DEMO = ROOT / "examples" / "speed_rate_demo.py"
OUT_DIR = ROOT / "yty_manim" / "examples" / "speed_rate"
MEDIA = ROOT / "media_speed_rate"

# 限制并行；Windows 下并行易撞 media/texts 缓存锁，默认 1
WORKERS = 1


def scene_names() -> list[str]:
    from yty_manim.disposition.speed_rate_fuc import rate_presets

    return [f"Rate_{n}" for n in rate_presets]


def render_one(scene: str) -> tuple[str, int, str]:
    cmd = [
        sys.executable,
        "-m",
        "manim",
        "render",
        str(DEMO),
        scene,
        "-ql",
        "--format",
        "gif",
        "--fps",
        "15",
        "--media_dir",
        str(MEDIA),
        "-o",
        scene,
        "--disable_caching",
    ]
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    return scene, proc.returncode, (proc.stderr or "")[-800:]


def collect_gifs() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    # manim 输出大致在 media_dir/videos/.../480p15/*.gif 或 images
    found = list(MEDIA.rglob("Rate_*.gif"))
    if not found:
        found = list(MEDIA.rglob("*.gif"))
    for src in found:
        # Rate_ease_in_cubic.gif → ease_in_cubic.gif
        name = src.stem
        if name.startswith("Rate_"):
            name = name[len("Rate_") :]
        dst = OUT_DIR / f"{name}.gif"
        shutil.copy2(src, dst)
        print(f"copied {dst.relative_to(ROOT)}")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    MEDIA.mkdir(parents=True, exist_ok=True)
    scenes = scene_names()
    print(f"rendering {len(scenes)} scenes, workers={WORKERS}")
    failed: list[tuple[str, str]] = []
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        futs = {pool.submit(render_one, s): s for s in scenes}
        for fut in as_completed(futs):
            scene, code, err = fut.result()
            if code == 0:
                print(f"OK  {scene}")
            else:
                print(f"FAIL {scene}")
                failed.append((scene, err))
    collect_gifs()
    if failed:
        print("\n--- failures ---")
        for s, e in failed:
            print(s, e)
        sys.exit(1)
    print(f"\nDONE → {OUT_DIR}")


if __name__ == "__main__":
    main()
