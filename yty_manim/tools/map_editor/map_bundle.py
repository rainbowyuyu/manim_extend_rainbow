# rainbow_yu — editable grid map bundle (export / import for Manim shockwave scenes)

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np

BUNDLE_VERSION = 1
DEFAULT_GRID_W = 128
DEFAULT_GRID_H = 96
DEFAULT_CELL_METERS = 0.625
DEFAULT_WAVE_SPEED = 27.5
DEFAULT_BG_RGB = (18, 18, 22)
DEFAULT_FLOOR_RGB = (72, 72, 78)
DEFAULT_OBSTACLE_RGB = (42, 38, 36)

_MAPS_ROOT = Path(__file__).resolve().parents[3] / "video_project" / "custom_maps"
_MIRAGE_DATA = Path(__file__).resolve().parents[3] / "video_project" / "cs2_c4" / "cs2_c4_data"


@dataclass
class MapMarker:
    id: str
    norm: tuple[float, float]
    label: str
    kind: str = "text"  # text | icon
    color: str = "#ffffff"
    icon: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "norm": list(self.norm),
            "label": self.label,
            "kind": self.kind,
            "color": self.color,
            "icon": self.icon,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> MapMarker:
        return cls(
            id=str(data["id"]),
            norm=(float(data["norm"][0]), float(data["norm"][1])),
            label=str(data.get("label", "")),
            kind=str(data.get("kind", "text")),
            color=str(data.get("color", "#ffffff")),
            icon=str(data.get("icon", "")),
        )


@dataclass
class ExplosionSource:
    id: str
    norm: tuple[float, float]
    label: str = "C4"
    color: str = "#ff6600"

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "norm": list(self.norm),
            "label": self.label,
            "color": self.color,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ExplosionSource:
        return cls(
            id=str(data["id"]),
            norm=(float(data["norm"][0]), float(data["norm"][1])),
            label=str(data.get("label", "C4")),
            color=str(data.get("color", "#ff6600")),
        )


@dataclass
class MapBundle:
    """Portable map package for editor export and Manim import."""

    map_name: str
    grid_w: int = DEFAULT_GRID_W
    grid_h: int = DEFAULT_GRID_H
    walkable: np.ndarray = field(default_factory=lambda: np.zeros((DEFAULT_GRID_H, DEFAULT_GRID_W), dtype=bool))
    cell_colors: np.ndarray = field(
        default_factory=lambda: np.full((DEFAULT_GRID_H, DEFAULT_GRID_W, 3), DEFAULT_BG_RGB, dtype=np.uint8)
    )
    explosion_sources: list[ExplosionSource] = field(default_factory=list)
    markers: list[MapMarker] = field(default_factory=list)
    cell_meters: float = DEFAULT_CELL_METERS
    wave_speed_m_s: float = DEFAULT_WAVE_SPEED

    def __post_init__(self) -> None:
        self.walkable = np.asarray(self.walkable, dtype=bool)
        self.cell_colors = np.asarray(self.cell_colors, dtype=np.uint8)
        if self.walkable.shape != (self.grid_h, self.grid_w):
            raise ValueError(f"walkable shape {self.walkable.shape} != ({self.grid_h}, {self.grid_w})")
        if self.cell_colors.shape != (self.grid_h, self.grid_w, 3):
            raise ValueError(f"cell_colors shape {self.cell_colors.shape} != ({self.grid_h}, {self.grid_w}, 3)")

    @property
    def bundle_dir(self) -> Path:
        return _MAPS_ROOT / self.map_name

    def norm_to_grid(self, nx: float, ny: float) -> tuple[int, int]:
        i = int(np.clip(nx * (self.grid_w - 1), 0, self.grid_w - 1))
        j = int(np.clip(ny * (self.grid_h - 1), 0, self.grid_h - 1))
        return i, j

    def grid_to_norm(self, i: int, j: int) -> tuple[float, float]:
        return i / max(self.grid_w - 1, 1), j / max(self.grid_h - 1, 1)

    def pixel_to_norm(self, px: int, py: int, canvas_w: int, canvas_h: int) -> tuple[float, float]:
        """Canvas pixel (origin top-left) -> normalized map coords (origin bottom-left)."""
        cell_w = canvas_w / self.grid_w
        cell_h = canvas_h / self.grid_h
        i = int(np.clip(px / cell_w, 0, self.grid_w - 1))
        j = int(np.clip((canvas_h - 1 - py) / cell_h, 0, self.grid_h - 1))
        return self.grid_to_norm(i, j)

    def primary_explosion(self) -> ExplosionSource | None:
        return self.explosion_sources[0] if self.explosion_sources else None

    def meta_dict(self) -> dict[str, Any]:
        return {
            "version": BUNDLE_VERSION,
            "map_name": self.map_name,
            "grid_w": self.grid_w,
            "grid_h": self.grid_h,
            "coord_system": "norm_bottom_left",
            "cell_meters": self.cell_meters,
            "wave_speed_m_s": self.wave_speed_m_s,
            "explosion_sources": [s.to_dict() for s in self.explosion_sources],
            "markers": [m.to_dict() for m in self.markers],
            "exported_at": datetime.now(timezone.utc).isoformat(),
        }

    def save(self, path: Path | None = None) -> Path:
        out = path or self.bundle_dir
        out.mkdir(parents=True, exist_ok=True)
        (out / "meta.json").write_text(
            json.dumps(self.meta_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        np.save(out / "walkable.npy", self.walkable)
        np.save(out / "cell_colors.npy", self.cell_colors)
        return out

    @classmethod
    def load(cls, path: Path) -> MapBundle:
        path = Path(path)
        meta_path = path / "meta.json"
        if not meta_path.exists():
            raise FileNotFoundError(f"Missing meta.json in {path}")
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        grid_w = int(meta["grid_w"])
        grid_h = int(meta["grid_h"])
        walk = np.load(path / "walkable.npy").astype(bool)
        colors_path = path / "cell_colors.npy"
        if colors_path.exists():
            colors = np.load(colors_path).astype(np.uint8)
        else:
            colors = np.full((grid_h, grid_w, 3), DEFAULT_BG_RGB, dtype=np.uint8)
        sources = [ExplosionSource.from_dict(s) for s in meta.get("explosion_sources", [])]
        markers = [MapMarker.from_dict(m) for m in meta.get("markers", [])]
        return cls(
            map_name=str(meta.get("map_name", path.name)),
            grid_w=grid_w,
            grid_h=grid_h,
            walkable=walk,
            cell_colors=colors,
            explosion_sources=sources,
            markers=markers,
            cell_meters=float(meta.get("cell_meters", DEFAULT_CELL_METERS)),
            wave_speed_m_s=float(meta.get("wave_speed_m_s", DEFAULT_WAVE_SPEED)),
        )

    @classmethod
    def blank(cls, name: str = "untitled", grid_w: int = DEFAULT_GRID_W, grid_h: int = DEFAULT_GRID_H) -> MapBundle:
        walk = np.zeros((grid_h, grid_w), dtype=bool)
        colors = np.full((grid_h, grid_w, 3), DEFAULT_BG_RGB, dtype=np.uint8)
        cx, cy = grid_w // 2, grid_h // 2
        r = min(grid_w, grid_h) // 8
        for j in range(grid_h):
            for i in range(grid_w):
                if (i - cx) ** 2 + (j - cy) ** 2 <= r ** 2:
                    walk[j, i] = True
                    colors[j, i] = DEFAULT_FLOOR_RGB
        source = ExplosionSource(id="bomb_1", norm=(0.5, 0.5), label="C4")
        return cls(
            map_name=name,
            grid_w=grid_w,
            grid_h=grid_h,
            walkable=walk,
            cell_colors=colors,
            explosion_sources=[source],
        )

    @classmethod
    def from_mirage(cls, name: str = "de_mirage_import") -> MapBundle:
        meta_path = _MIRAGE_DATA / "mirage_radar_meta.json"
        if not meta_path.exists():
            raise FileNotFoundError("Mirage data missing. Run build_radar_walkability.py first.")
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        grid_w = int(meta["grid_w"])
        grid_h = int(meta["grid_h"])
        walk = np.load(_MIRAGE_DATA / "mirage_walkable.npy").astype(bool)
        colors_path = _MIRAGE_DATA / "mirage_cell_colors.npy"
        if colors_path.exists():
            colors = np.load(colors_path).astype(np.uint8)
        else:
            colors = np.full((grid_h, grid_w, 3), DEFAULT_FLOOR_RGB, dtype=np.uint8)
            colors[~walk] = DEFAULT_BG_RGB

        sources: list[ExplosionSource] = []
        markers: list[MapMarker] = []
        for key, site in meta.get("sites", {}).items():
            norm = (float(site["norm"][0]), float(site["norm"][1]))
            label = str(site.get("label", key))
            if key.upper() == "A":
                sources.append(ExplosionSource(id="bomb_a", norm=norm, label="C4", color="#ff6600"))
            else:
                markers.append(MapMarker(id=key, norm=norm, label=label, kind="text", color="#66ccff"))

        if not sources and "A" in meta.get("sites", {}):
            s = meta["sites"]["A"]
            sources.append(
                ExplosionSource(
                    id="bomb_a",
                    norm=(float(s["norm"][0]), float(s["norm"][1])),
                    label="C4",
                )
            )

        return cls(
            map_name=name,
            grid_w=grid_w,
            grid_h=grid_h,
            walkable=walk,
            cell_colors=colors,
            explosion_sources=sources,
            markers=markers,
        )


def default_maps_dir() -> Path:
    path = _MAPS_ROOT
    path.mkdir(parents=True, exist_ok=True)
    return path


def list_saved_maps() -> list[Path]:
    root = default_maps_dir()
    return sorted(p for p in root.iterdir() if p.is_dir() and (p / "meta.json").exists())


def duplicate_bundle(src: Path, dst_name: str) -> MapBundle:
    bundle = MapBundle.load(src)
    bundle.map_name = dst_name
    dst = default_maps_dir() / dst_name
    if dst.exists():
        shutil.rmtree(dst)
    bundle.save(dst)
    return bundle
