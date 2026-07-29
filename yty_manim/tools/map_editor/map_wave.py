# rainbow_yu — generic Dijkstra shockwave on editable map bundles

from __future__ import annotations

import heapq

import numpy as np

from yty_manim.tools.map_editor.map_bundle import MapBundle, MapMarker


def snap_walkable(bundle: MapBundle, i: int, j: int) -> tuple[int, int]:
    if bundle.walkable[j, i]:
        return i, j
    for radius in range(1, 12):
        for dj in range(-radius, radius + 1):
            for di in range(-radius, radius + 1):
                ni, nj = i + di, j + dj
                if (
                    0 <= ni < bundle.grid_w
                    and 0 <= nj < bundle.grid_h
                    and bundle.walkable[nj, ni]
                ):
                    return ni, nj
    return i, j


def dijkstra_wave_field(
    bundle: MapBundle,
    source_norm: tuple[float, float],
) -> tuple[np.ndarray, np.ndarray]:
    """Returns (dist_grid, intensity_grid). Unreachable cells = inf / 0."""
    gw, gh = bundle.grid_w, bundle.grid_h
    walk = bundle.walkable
    si, sj = bundle.norm_to_grid(*source_norm)
    si, sj = snap_walkable(bundle, si, sj)

    dist = np.full((gh, gw), np.inf, dtype=float)
    dist[sj, si] = 0.0
    pq: list[tuple[float, int, int]] = [(0.0, si, sj)]
    moves = [
        (1, 0, 1.0), (-1, 0, 1.0), (0, 1, 1.0), (0, -1, 1.0),
        (1, 1, 1.414), (1, -1, 1.414), (-1, 1, 1.414), (-1, -1, 1.414),
    ]

    while pq:
        d, i, j = heapq.heappop(pq)
        if d > dist[j, i]:
            continue
        for di, dj, cost in moves:
            ni, nj = i + di, j + dj
            if 0 <= ni < gw and 0 <= nj < gh and walk[nj, ni]:
                nd = d + cost
                if nd < dist[nj, ni]:
                    dist[nj, ni] = nd
                    heapq.heappush(pq, (nd, ni, nj))

    finite = dist[np.isfinite(dist)]
    max_d = float(finite.max()) if finite.size else 1.0
    intensity = np.zeros_like(dist)
    mask = np.isfinite(dist)
    intensity[mask] = np.clip(1.0 - dist[mask] / max_d, 0, 1) ** 0.82
    return dist, intensity


def intensity_to_damage(intensity: float) -> int:
    if intensity <= 0:
        return 0
    if intensity >= 1.0:
        return 255
    if intensity <= 0.2:
        return int(165 * intensity)
    if intensity <= 0.4:
        return int(33 + (intensity - 0.2) * 220)
    if intensity <= 0.7:
        return int(77 + (intensity - 0.4) * 200)
    return int(137 + (intensity - 0.7) * 393)


def grid_dist_to_meters(bundle: MapBundle, d: float) -> float:
    return d * bundle.cell_meters


def arrival_time_seconds(bundle: MapBundle, path_dist_grid: float) -> float:
    return grid_dist_to_meters(bundle, path_dist_grid) / bundle.wave_speed_m_s


def shockwave_field(
    bundle: MapBundle,
    source_norm: tuple[float, float] | None = None,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Returns (dist, intensity, damage_power) for custom maps."""
    if source_norm is None:
        primary = bundle.primary_explosion()
        if primary is None:
            raise ValueError("Map has no explosion source. Place one in the editor.")
        source_norm = primary.norm
    dist, intensity = dijkstra_wave_field(bundle, source_norm)
    damage = np.zeros((bundle.grid_h, bundle.grid_w), dtype=np.int32)
    mask = np.isfinite(dist)
    dmg_vals = np.vectorize(intensity_to_damage)(intensity[mask])
    damage[mask] = dmg_vals.astype(np.int32)
    return dist, intensity, damage


def sample_at_marker(
    bundle: MapBundle,
    marker: MapMarker,
    dist: np.ndarray,
    intensity: np.ndarray,
    damage: np.ndarray,
) -> tuple[float, float, int, float]:
    i, j = bundle.norm_to_grid(*marker.norm)
    i, j = snap_walkable(bundle, i, j)
    d = float(dist[j, i]) if np.isfinite(dist[j, i]) else float("inf")
    inten = float(intensity[j, i]) if np.isfinite(d) else 0.0
    dmg = int(damage[j, i]) if np.isfinite(d) else 0
    return d, inten, dmg, arrival_time_seconds(bundle, d)
