# CS2 Baked Bomb Damage — Extraction Report

## Compile Pipeline

`game/csgo_core/gameinfo.gi` → `GameSpecificPostMapBuildSteps` → `cs2_bomb_damage`

## Maps With `baked_bomb_damage` Resource

- `de_ancient`
- `de_ancient_night`
- `de_anubis`
- `de_cache`
- `de_dust2`
- `de_inferno`
- `de_mirage`
- `de_nuke`
- `de_overpass`
- `de_train`
- `de_vertigo`

## Mirage Related Strings (from VPK binary scan)

- `_damage_power`
- `baked_bomb_damage`
- `bombsite`
- `bombsite_a.vmaj`
- `bombsite_b.vmaj`
- `bombsite_left_arrow.vmatr`
- `bombsite_letter_a.vmatp`
- `bombsite_letter_b.vmatp`
- `bombsite_line_spray.vmatr`
- `bombsiteb`
- `content/csgo/maps/de_mirage/baked_bomb_damage.vdata`
- `maps/de_mirage/baked_bomb_damage.vdata`
- `materials/decals/bombsite_a.vmat`
- `materials/decals/bombsite_b.vmat`
- `materials/decals/bombsite_left_arrow.vmat`
- `materials/decals/bombsite_letter_a.vmat`
- `materials/decals/bombsite_letter_b.vmat`
- `materials/decals/bombsite_line_spray.vmat`
- `materials/decals/bombsite_right_arrow.vmat`

## SkinSniper Cross-Validation

Compare in-game `cl_bake_bomb_damage_debug 1` overlay with:
https://skinsniper.com/tools/bomb-damage-radius (Mirage · Site A)

| Intensity | Approx HP |
|-----------|-----------|
| 20% | ~33 |
| 40% | ~77 |
| 100% | lethal (>100) |

## Source2Viewer Next Step

1. Open `de_mirage.vpk` in Source2Viewer
2. Search resource tree for `baked_bomb_damage`
3. Export raw bytes for Manim heatmap overlay (optional)
