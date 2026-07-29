# rainbow_yu — drawing helpers for map editor

from __future__ import annotations

import copy
from dataclasses import dataclass, field

import numpy as np

from yty_manim.tools.map_editor.map_bundle import (
    DEFAULT_BG_RGB,
    DEFAULT_FLOOR_RGB,
    DEFAULT_OBSTACLE_RGB,
    ExplosionSource,
    MapBundle,
    MapMarker,
)


@dataclass
class MapSnapshot:
    walkable: np.ndarray
    cell_colors: np.ndarray
    explosion_sources: list[ExplosionSource] = field(default_factory=list)
    markers: list[MapMarker] = field(default_factory=list)


def snapshot(bundle: MapBundle) -> MapSnapshot:
    return MapSnapshot(
        walkable=bundle.walkable.copy(),
        cell_colors=bundle.cell_colors.copy(),
        explosion_sources=copy.deepcopy(bundle.explosion_sources),
        markers=copy.deepcopy(bundle.markers),
    )


def restore(bundle: MapBundle, snap: MapSnapshot) -> None:
    bundle.walkable[:] = snap.walkable
    bundle.cell_colors[:] = snap.cell_colors
    bundle.explosion_sources = copy.deepcopy(snap.explosion_sources)
    bundle.markers = copy.deepcopy(snap.markers)


def bresenham_line(i0: int, j0: int, i1: int, j1: int) -> list[tuple[int, int]]:
    cells: list[tuple[int, int]] = []
    di = abs(i1 - i0)
    dj = abs(j1 - j0)
    si = 1 if i0 < i1 else -1
    sj = 1 if j0 < j1 else -1
    err = di - dj
    i, j = i0, j0
    while True:
        cells.append((i, j))
        if i == i1 and j == j1:
            break
        e2 = 2 * err
        if e2 > -dj:
            err -= dj
            i += si
        if e2 < di:
            err += di
            j += sj
    return cells


def _brush_offsets(brush_size: int, *, square: bool) -> list[tuple[int, int]]:
    """brush_size=N spans N cells across; N=1 is exactly one cell."""
    if brush_size <= 1:
        return [(0, 0)]
    r0 = -brush_size // 2
    r1 = (brush_size - 1) // 2
    offsets: list[tuple[int, int]] = []
    for dj in range(r0, r1 + 1):
        for di in range(r0, r1 + 1):
            if square:
                offsets.append((di, dj))
            elif di * di + dj * dj <= r1 * r1:
                offsets.append((di, dj))
    return offsets


def stamp_brush(
    bundle: MapBundle,
    i: int,
    j: int,
    brush_size: int,
    *,
    walkable: bool,
    rgb: tuple[int, int, int],
    square: bool = False,
) -> None:
    gw, gh = bundle.grid_w, bundle.grid_h
    for di, dj in _brush_offsets(brush_size, square=square):
        ni, nj = i + di, j + dj
        if 0 <= ni < gw and 0 <= nj < gh:
            bundle.walkable[nj, ni] = walkable
            bundle.cell_colors[nj, ni] = rgb


def stamp_disc(
    bundle: MapBundle,
    i: int,
    j: int,
    radius: int,
    *,
    walkable: bool,
    rgb: tuple[int, int, int],
) -> None:
    stamp_brush(bundle, i, j, radius, walkable=walkable, rgb=rgb, square=False)


def stamp_line(
    bundle: MapBundle,
    i0: int,
    j0: int,
    i1: int,
    j1: int,
    brush_size: int,
    *,
    walkable: bool,
    rgb: tuple[int, int, int],
    square: bool = False,
) -> None:
    for ci, cj in bresenham_line(i0, j0, i1, j1):
        stamp_brush(bundle, ci, cj, brush_size, walkable=walkable, rgb=rgb, square=square)


def stamp_box(
    bundle: MapBundle,
    center_i: int,
    center_j: int,
    width: int,
    height: int,
    *,
    walkable: bool,
    rgb: tuple[int, int, int],
) -> None:
    """Place axis-aligned square/rect obstacle centered on grid cell."""
    gw, gh = bundle.grid_w, bundle.grid_h
    i0 = center_i - width // 2
    j0 = center_j - height // 2
    for dj in range(height):
        for di in range(width):
            ni, nj = i0 + di, j0 + dj
            if 0 <= ni < gw and 0 <= nj < gh:
                bundle.walkable[nj, ni] = walkable
                bundle.cell_colors[nj, ni] = rgb


def fill_region(
    bundle: MapBundle,
    i: int,
    j: int,
    *,
    walkable: bool,
    rgb: tuple[int, int, int],
    match_walkable: bool | None = None,
) -> int:
    """Flood fill connected region. Returns cells changed."""
    gw, gh = bundle.grid_w, bundle.grid_h
    if not (0 <= i < gw and 0 <= j < gh):
        return 0
    if match_walkable is None:
        match_walkable = bool(bundle.walkable[j, i])
    target = match_walkable
    if target == walkable and tuple(bundle.cell_colors[j, i]) == rgb:
        return 0

    stack = [(i, j)]
    seen = set()
    changed = 0
    while stack:
        ci, cj = stack.pop()
        if (ci, cj) in seen:
            continue
        seen.add((ci, cj))
        if not (0 <= ci < gw and 0 <= cj < gh):
            continue
        if bool(bundle.walkable[cj, ci]) != target:
            continue
        bundle.walkable[cj, ci] = walkable
        bundle.cell_colors[cj, ci] = rgb
        changed += 1
        stack.extend([(ci + 1, cj), (ci - 1, cj), (ci, cj + 1), (ci, cj - 1)])
    return changed


def fill_rect(
    bundle: MapBundle,
    i0: int,
    j0: int,
    i1: int,
    j1: int,
    *,
    walkable: bool,
    rgb: tuple[int, int, int],
) -> None:
    ia, ib = sorted((i0, i1))
    ja, jb = sorted((j0, j1))
    gw, gh = bundle.grid_w, bundle.grid_h
    for j in range(max(0, ja), min(gh, jb + 1)):
        for i in range(max(0, ia), min(gw, ib + 1)):
            bundle.walkable[j, i] = walkable
            bundle.cell_colors[j, i] = rgb


def pick_cell_color(bundle: MapBundle, i: int, j: int) -> tuple[int, int, int]:
    return tuple(int(v) for v in bundle.cell_colors[j, i])


def is_obstacle_cell(bundle: MapBundle, j: int, i: int) -> bool:
    """Colored non-walkable cell — blocks shockwave pathfinding."""
    if bundle.walkable[j, i]:
        return False
    return tuple(int(v) for v in bundle.cell_colors[j, i]) != DEFAULT_BG_RGB


def is_floor_cell(bundle: MapBundle, j: int, i: int) -> bool:
    return bool(bundle.walkable[j, i])


def is_exterior_cell(bundle: MapBundle, j: int, i: int) -> bool:
    return not bundle.walkable[j, i] and not is_obstacle_cell(bundle, j, i)


def nearest_marker(
    bundle: MapBundle,
    nx: float,
    ny: float,
    threshold: float = 0.035,
) -> ExplosionSource | MapMarker | None:
    best = None
    best_d = threshold ** 2
    for src in bundle.explosion_sources:
        d = (src.norm[0] - nx) ** 2 + (src.norm[1] - ny) ** 2
        if d < best_d:
            best_d = d
            best = src
    for m in bundle.markers:
        d = (m.norm[0] - nx) ** 2 + (m.norm[1] - ny) ** 2
        if d < best_d:
            best_d = d
            best = m
    return best
