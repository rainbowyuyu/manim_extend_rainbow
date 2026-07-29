# CS2 C4 Shockwave — Advanced compose (PiP + crossfade + narration)
# Usage: .\compose_video.ps1
# Requires: ffmpeg, manim clips in manim/, optional raw/ footage

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$ManimDir = Join-Path $Root "manim"
$RawDir = Join-Path (Split-Path $Root) "cs2_c4_footage\raw"
$OutDir = Join-Path $Root "output"
$AudioDir = Join-Path $Root "audio"
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

function Get-Clip {
    param([string]$Raw, [string]$Manim)
    $r = Join-Path $RawDir $Raw
    if ($Raw -and (Test-Path $r)) { return $r }
    $m = Join-Path $ManimDir $Manim
    if (Test-Path $m) { return $m }
    return $null
}

function Overlay-Pip {
    param(
        [string]$BaseVideo,
        [string]$OverlayVideo,
        [string]$OutFile,
        [string]$OverlayPos = "W-640:40"
    )
    if (-not (Test-Path $BaseVideo)) { return $null }
    if (-not (Test-Path $OverlayVideo)) {
        Copy-Item $BaseVideo $OutFile -Force
        return $OutFile
    }
    ffmpeg -y -i $BaseVideo -i $OverlayVideo -filter_complex `
        "[1:v]scale=640:-1[ov];[0:v][ov]overlay=$OverlayPos:format=auto" `
        -c:a copy $OutFile 2>$null
    if (Test-Path $OutFile) { return $OutFile }
    Copy-Item $BaseVideo $OutFile -Force
    return $OutFile
}

function Xfade-Two {
    param([string]$A, [string]$B, [string]$Out, [double]$Duration = 0.4)
    if (-not (Test-Path $A)) { return $B }
    if (-not (Test-Path $B)) { return $A }
    ffmpeg -y -i $A -i $B -filter_complex `
        "xfade=transition=fade:duration=$Duration:offset=0" `
        -c:v libx264 -crf 18 -preset fast -c:a aac $Out 2>$null
    if (Test-Path $Out) { return $Out }
    return $A
}

$work = Join-Path $OutDir "compose_work"
New-Item -ItemType Directory -Force -Path $work | Out-Null

# Shot 01: gameplay base + Manim intro overlay (top-right)
$introManim = Join-Path $ManimDir "IntroHookScene.mp4"
$explosion = Get-Clip "mirage_a_explosion_wave.mp4" "IntroHookScene.mp4"
$shot01 = Join-Path $work "01_hook.mp4"
if ((Get-Clip "mirage_a_explosion_wave.mp4" "") -and (Test-Path $introManim)) {
    Overlay-Pip -BaseVideo (Get-Clip "mirage_a_explosion_wave.mp4" "") `
        -OverlayVideo $introManim -OutFile $shot01 -OverlayPos "W-720:30"
} else {
    if (Test-Path $introManim) { Copy-Item $introManim $shot01 -Force }
}

$segmentFiles = @()
if (Test-Path $shot01) { $segmentFiles += $shot01 }

foreach ($pair in @(
    @("02", "OldVsNewBombScene.mp4"),
    @("03", "PatchTimelineScene.mp4"),
    @("03b", "SourcePipelineScene.mp4"),
    @("06", "MapBakeBFSScene.mp4"),
    @("07", "RuntimeLookupScene.mp4"),
    @("09", "DamageCurveScene.mp4"),
    @("10", "MirageShockwaveDemoScene.mp4")
)) {
    $p = Join-Path $ManimDir $pair[1]
    if (Test-Path $p) { $segmentFiles += $p }
}

# Shot 04: debug footage + evidence manim PiP bottom-left
$debug = Get-Clip "mirage_a_debug_wide.mp4" "GameEvidenceScene.mp4"
$evidence = Join-Path $ManimDir "GameEvidenceScene.mp4"
$shot04 = Join-Path $work "04_debug.mp4"
if ((Get-Clip "mirage_a_debug_wide.mp4" "") -and (Test-Path $evidence)) {
    Overlay-Pip -BaseVideo (Get-Clip "mirage_a_debug_wide.mp4" "") `
        -OverlayVideo $evidence -OutFile $shot04 -OverlayPos "40:H-380"
} elseif (Test-Path $evidence) {
    Copy-Item $evidence $shot04 -Force
}
if (Test-Path $shot04) { $segmentFiles += $shot04 }

# Shot 05/08 handled by build_video concat; append manim fallbacks if needed
$three = Join-Path $ManimDir "ThreePositionScene.mp4"
if (Test-Path $three) { $segmentFiles += $three }
$hud = Join-Path $ManimDir "DamagePreviewHUDScene.mp4"
if (Test-Path $hud) { $segmentFiles += $hud }

$outro = Get-Clip "mirage_a_explosion_wave.mp4" "OutroScene.mp4"
if (Test-Path (Join-Path $ManimDir "OutroScene.mp4")) {
    $segmentFiles += (Join-Path $ManimDir "OutroScene.mp4")
}

# Sequential xfade merge (simple chain)
$merged = $segmentFiles | Where-Object { $_ -and (Test-Path $_) }
if ($merged.Count -eq 0) {
    Write-Error "No clips found. Run render_all.bat first."
}
$current = $merged[0]
for ($i = 1; $i -lt $merged.Count; $i++) {
    $nextOut = Join-Path $work ("xfade_" + $i + ".mp4")
    $current = Xfade-Two -A $current -B $merged[$i] -Out $nextOut
}

$composed = Join-Path $OutDir "cs2_c4_shockwave_composed.mp4"
Copy-Item $current $composed -Force

$narration = Join-Path $AudioDir "narration.wav"
if (Test-Path $narration) {
    $withAudio = Join-Path $OutDir "cs2_c4_shockwave_composed_narrated.mp4"
    ffmpeg -y -i $composed -i $narration -c:v copy -c:a aac -b:a 192k `
        -map 0:v:0 -map 1:a:0 -shortest $withAudio
    Write-Host "Narrated: $withAudio"
}

Write-Host "Composed: $composed"
