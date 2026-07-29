#!/usr/bin/env python3
"""Extract baked bomb damage metadata from CS2 map VPK files."""

from __future__ import annotations

import json
import re
import struct
import sys
from pathlib import Path

CS2_MAPS = Path(
    r"D:\stream\steamapps\common\Counter-Strike Global Offensive\game\csgo\maps"
)
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "cs2_c4_data"


def read_ascii_strings(data: bytes, min_len: int = 6) -> list[str]:
    pattern = re.compile(rb"[\x20-\x7E]{%d,}" % min_len)
    return [m.group().decode("ascii", errors="ignore") for m in pattern.finditer(data)]


def scan_vpk(vpk_path: Path) -> dict:
    data = vpk_path.read_bytes()
    strings = read_ascii_strings(data)
    keywords = (
        "baked_bomb_damage",
        "damage_power",
        "bombsite",
        "bake_bomb",
        "damage_prediction",
    )
    hits = sorted({s for s in strings if any(k in s.lower() for k in keywords)})
    return {
        "map": vpk_path.stem,
        "size_mb": round(len(data) / 1024 / 1024, 2),
        "has_baked_bomb_damage": "baked_bomb_damage" in data.decode("latin-1", errors="ignore"),
        "related_strings": hits[:40],
    }


def parse_vpk_dir(vpk_path: Path) -> list[dict]:
    """Parse VPK directory table for entries containing bomb damage."""
    data = vpk_path.read_bytes()
    if data[:4] != b"VPK\x00":
        return []

    version = struct.unpack_from("<I", data, 4)[0]
    if version not in (1, 2):
        return []

    tree_size = struct.unpack_from("<I", data, 8)[0]
    tree_start = 12
    tree_end = tree_start + tree_size
    tree = data[tree_start:tree_end].decode("latin-1", errors="ignore")

    entries = []
    for part in tree.split("\x00"):
        if not part or "/" not in part:
            continue
        lower = part.lower()
        if any(k in lower for k in ("bomb", "damage", "bake")):
            entries.append(part)
    return [{"path_fragment": e} for e in sorted(set(entries))[:60]]


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    results = []

    if not CS2_MAPS.exists():
        print(f"CS2 maps path not found: {CS2_MAPS}", file=sys.stderr)
        return 1

    for vpk in sorted(CS2_MAPS.glob("de_*.vpk")):
        if "vanity" in vpk.name:
            continue
        info = scan_vpk(vpk)
        if info["has_baked_bomb_damage"]:
            info["vpk_entries"] = parse_vpk_dir(vpk)
        results.append(info)
        print(f"[{info['map']}] baked_bomb_damage={'YES' if info['has_baked_bomb_damage'] else 'no'}")

    mirage = next((r for r in results if r["map"] == "de_mirage"), None)
    summary = {
        "source": str(CS2_MAPS),
        "maps_scanned": len(results),
        "maps_with_baked_bomb_damage": [r["map"] for r in results if r["has_baked_bomb_damage"]],
        "mirage_detail": mirage,
        "skinsniper_crosscheck": {
            "url": "https://skinsniper.com/tools/bomb-damage-radius",
            "mirage_site_a_notes": [
                "Blast field comes from map shipped data (same as cl_bake_bomb_damage_debug)",
                "~33 HP at 20% intensity, ~77 HP at 40% intensity (approximate)",
                "Lethal zone: wave travel 33-77m depending on site, then fades over ~32m",
                "Armor does not reduce bomb damage",
            ],
        },
        "compile_pipeline": {
            "file": "game/csgo_core/gameinfo.gi",
            "step": "cs2_bomb_damage",
            "location": "GameSpecificPostMapBuildSteps",
        },
    }

    out_json = OUTPUT_DIR / "baked_bomb_damage_scan.json"
    out_json.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    md_lines = [
        "# CS2 Baked Bomb Damage — Extraction Report",
        "",
        "## Compile Pipeline",
        "",
        "`game/csgo_core/gameinfo.gi` → `GameSpecificPostMapBuildSteps` → `cs2_bomb_damage`",
        "",
        "## Maps With `baked_bomb_damage` Resource",
        "",
    ]
    for name in summary["maps_with_baked_bomb_damage"]:
        md_lines.append(f"- `{name}`")
    md_lines.extend(
        [
            "",
            "## Mirage Related Strings (from VPK binary scan)",
            "",
        ]
    )
    if mirage:
        for s in mirage.get("related_strings", []):
            md_lines.append(f"- `{s}`")
    md_lines.extend(
        [
            "",
            "## SkinSniper Cross-Validation",
            "",
            "Compare in-game `cl_bake_bomb_damage_debug 1` overlay with:",
            "https://skinsniper.com/tools/bomb-damage-radius (Mirage · Site A)",
            "",
            "| Intensity | Approx HP |",
            "|-----------|-----------|",
            "| 20% | ~33 |",
            "| 40% | ~77 |",
            "| 100% | lethal (>100) |",
            "",
            "## Source2Viewer Next Step",
            "",
            "1. Open `de_mirage.vpk` in Source2Viewer",
            "2. Search resource tree for `baked_bomb_damage`",
            "3. Export raw bytes for Manim heatmap overlay (optional)",
            "",
        ]
    )
    (OUTPUT_DIR / "EXTRACTION_REPORT.md").write_text("\n".join(md_lines), encoding="utf-8")
    print(f"\nWrote {out_json}")
    print(f"Wrote {OUTPUT_DIR / 'EXTRACTION_REPORT.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
