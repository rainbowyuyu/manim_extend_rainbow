#!/usr/bin/env python3
"""Extract baked_bomb_damage from de_mirage.vpk and rasterize to radar grid."""

from __future__ import annotations

import io
import json
import struct
import sys
from pathlib import Path

import numpy as np

try:
    import keyvalues3 as kv3
except ImportError:
    raise SystemExit("pip install keyvalues3")

try:
    import vpk
except ImportError:
    raise SystemExit("pip install vpk")

try:
    import zstandard as zstd
except ImportError:
    raise SystemExit("pip install zstandard")

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "cs2_c4_data"
CS2_VPK = Path(
    r"D:\stream\steamapps\common\Counter-Strike Global Offensive\game\csgo\maps\de_mirage.vpk"
)
VPK_ENTRY = "maps/de_mirage/baked_bomb_damage.vdata_c"
GRID_W, GRID_H = 128, 96

# Per-cell layout in damage_values blob (8 bytes). Byte 4 tracks in-game damage_power best.
DAMAGE_BYTE_OFFSET = 4


def _align(v: int, a: int) -> int:
    return (v + a - 1) & ~(a - 1)


def parse_vrf_blocks(raw: bytes) -> dict[str, bytes]:
    header_ver, = struct.unpack_from("<H", raw, 4)
    if header_ver != 12:
        raise ValueError(f"unexpected header version {header_ver}")
    block_offset, = struct.unpack_from("<I", raw, 8)
    block_count, = struct.unpack_from("<I", raw, 12)
    pos = 16 + block_offset - 8
    blocks: dict[str, bytes] = {}
    for _ in range(block_count):
        btype = raw[pos : pos + 4]
        pos += 4
        rel_off, = struct.unpack_from("<I", raw, pos)
        pos += 4
        size, = struct.unpack_from("<I", raw, pos)
        pos += 4
        abs_off = (pos - 8) + rel_off
        blocks[btype.decode("ascii", errors="replace")] = raw[abs_off : abs_off + size]
    return blocks


def decode_kv3_v5_zstd(data: bytes) -> tuple[list[str], bytes, bytes, bytes]:
    magic, = struct.unpack_from("<I", data, 0)
    if (magic & 0xFFFFFF00) != 0x4B563300:
        raise ValueError(f"not KV3 magic: {hex(magic)}")
    version = magic & 0xFF
    if version != 5:
        raise ValueError(f"unsupported KV3 version {version}")

    pos = 4 + 16 + 4 + 4
    _, _, _, _ = struct.unpack_from("<iiii", data, pos)
    pos += 16
    pos += 4
    _, _, _, size_blobs = struct.unpack_from("<iiii", data, pos)
    pos += 16
    pos += 8
    su1, sc1, su2, sc2 = struct.unpack_from("<iiii", data, pos)
    pos += 16
    pos += 20

    dctx = zstd.ZstdDecompressor()
    pos += sc1
    pos += sc2
    blob_comp = size_blobs
    blobs = (
        dctx.decompress(data[pos : pos + blob_comp], max_output_size=size_blobs)
        if size_blobs
        else b""
    )

    obj = kv3.read(io.BytesIO(data))
    strings = list(obj.value.keys()) if False else []  # noqa: placeholder
    # strings from KV root for metadata only
    def collect_strings(v, out: list[str]) -> None:
        if isinstance(v, str) and v not in out:
            out.append(v)
        elif isinstance(v, dict):
            for val in v.values():
                collect_strings(val, out)
        elif isinstance(v, list):
            for val in v:
                collect_strings(val, out)

    collect_strings(obj.value, strings)
    return strings, b"", b"", blobs


def parse_kv3_blobs(data_block: bytes) -> dict[str, bytes]:
    obj = kv3.read(io.BytesIO(data_block))
    root = obj.value
    payload = root.get("data") or root.get("Data") or {}
    if not isinstance(payload, dict):
        raise ValueError("KV3 root has no data object")

    blobs: dict[str, bytes] = {}
    for key in ("bombsites", "positions", "damage_values"):
        val = payload.get(key)
        if isinstance(val, (bytes, bytearray)):
            blobs[key] = bytes(val)
        elif val is not None:
            raise TypeError(f"{key} expected bytes blob, got {type(val)}")
    return blobs


def _world_bounds(coords: np.ndarray) -> tuple[float, float, float, float]:
    return (
        float(coords[:, 0].min()),
        float(coords[:, 0].max()),
        float(coords[:, 1].min()),
        float(coords[:, 1].max()),
    )


def rasterize_site_a(
    positions: bytes,
    damage_values: bytes,
    grid_w: int = GRID_W,
    grid_h: int = GRID_H,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, dict]:
    """Project baked cells onto radar grid. Returns grids + per-cell arrays."""
    coords = np.frombuffer(positions, dtype=np.int16).reshape(-1, 3)
    dmg = np.frombuffer(damage_values, dtype=np.uint8).reshape(-1, 8)
    if coords.shape[0] != dmg.shape[0]:
        raise ValueError(f"cell count mismatch: {coords.shape[0]} vs {dmg.shape[0]}")

    power = dmg[:, DAMAGE_BYTE_OFFSET].astype(np.uint8)
    xmin, xmax, ymin, ymax = _world_bounds(coords)
    cell_norms = np.column_stack(
        (
            (coords[:, 0] - xmin) / max(xmax - xmin, 1.0),
            (coords[:, 1] - ymin) / max(ymax - ymin, 1.0),
        )
    ).astype(np.float32)

    damage_grid = np.zeros((grid_h, grid_w), dtype=np.uint8)
    count_grid = np.zeros((grid_h, grid_w), dtype=np.uint16)

    try:
        from scipy.spatial import cKDTree

        tree = cKDTree(cell_norms)
        for j in range(grid_h):
            for i in range(grid_w):
                nx = i / max(grid_w - 1, 1)
                ny = j / max(grid_h - 1, 1)
                dist, idx = tree.query((nx, ny), k=1)
                if dist <= 0.028:
                    damage_grid[j, i] = power[idx]
                    count_grid[j, i] = 1
    except ImportError:
        gi = np.clip(np.round(cell_norms[:, 0] * (grid_w - 1)).astype(int), 0, grid_w - 1)
        gj = np.clip(np.round(cell_norms[:, 1] * (grid_h - 1)).astype(int), 0, grid_h - 1)
        for p, i, j in zip(power, gi, gj):
            if p > damage_grid[j, i]:
                damage_grid[j, i] = p
            count_grid[j, i] += 1

    meta = {
        "cell_count": int(coords.shape[0]),
        "world_bounds": {"xmin": xmin, "xmax": xmax, "ymin": ymin, "ymax": ymax},
        "damage_byte_offset": DAMAGE_BYTE_OFFSET,
        "damage_min": int(power.min()),
        "damage_max": int(power.max()),
        "grid_w": grid_w,
        "grid_h": grid_h,
        "site": "A",
    }
    return damage_grid, count_grid, cell_norms, power, meta


def extract_from_vpk(vpk_path: Path = CS2_VPK) -> bytes:
    pak = vpk.open(str(vpk_path))
    return pak[VPK_ENTRY].read()


def export_mirage_site_a(
    vpk_path: Path = CS2_VPK,
    out_npz: Path | None = None,
) -> dict:
    if not vpk_path.exists():
        raise FileNotFoundError(f"CS2 VPK not found: {vpk_path}")

    raw = extract_from_vpk(vpk_path)
    blocks = parse_vrf_blocks(raw)
    data_block = blocks.get("DATA")
    if not data_block:
        raise ValueError("DATA block missing")

    blobs = parse_kv3_blobs(data_block)
    bombsites = blobs.get("bombsites", b"")
    positions = blobs["positions"]
    damage_values = blobs["damage_values"]

    damage_grid, count_grid, cell_norms, cell_power, meta = rasterize_site_a(positions, damage_values)
    meta.update(
        {
            "source": VPK_ENTRY,
            "vpk_path": str(vpk_path),
            "bombsites_bytes": len(bombsites),
            "positions_bytes": len(positions),
            "damage_values_bytes": len(damage_values),
            "bombsites_floats": list(struct.unpack(f"<{len(bombsites)//4}f", bombsites))
            if len(bombsites) % 4 == 0
            else [],
        }
    )

    out_npz = out_npz or DATA_DIR / "mirage_baked_site_a.npz"
    np.savez_compressed(
        out_npz,
        damage_power=damage_grid,
        sample_count=count_grid,
        cell_norms=cell_norms,
        cell_power=cell_power,
    )

    meta_path = DATA_DIR / "mirage_baked_site_a_meta.json"
    meta_path.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")

    (DATA_DIR / "baked_bomb_damage_mirage_a_raw.bin").write_bytes(raw)
    return meta


def main() -> int:
    if not CS2_VPK.exists():
        print(f"CS2 VPK not found: {CS2_VPK}", file=sys.stderr)
        return 1

    meta = export_mirage_site_a()
    print(json.dumps(meta, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
