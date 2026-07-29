# CS2 C4 Shockwave — Video Assembly Script (12 segments)
# Requires: ffmpeg in PATH
# Usage: .\build_video.ps1

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$ManimDir = Join-Path $Root "manim"
$RawDir = Join-Path (Split-Path $Root) "cs2_c4_footage\raw"
$OutDir = Join-Path $Root "output"
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
New-Item -ItemType Directory -Force -Path $ManimDir | Out-Null
New-Item -ItemType Directory -Force -Path $RawDir | Out-Null

function Invoke-Ffmpeg {
    param([string[]]$Cmd)
    $prev = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    & ffmpeg @Cmd 2>&1 | Out-Null
    $ErrorActionPreference = $prev
    if ($LASTEXITCODE -ne 0) {
        throw "ffmpeg failed (exit $LASTEXITCODE): ffmpeg $($Cmd -join ' ')"
    }
}

function Resolve-Clip {
    param([string]$RawName, [string]$ManimFallback, [string]$ManimFallback2 = "")
    $raw = Join-Path $RawDir $RawName
    if (Test-Path $raw) { return $raw }
    $p1 = Join-Path $ManimDir $ManimFallback
    if (Test-Path $p1) { return $p1 }
    if ($ManimFallback2) {
        $p2 = Join-Path $ManimDir $ManimFallback2
        if (Test-Path $p2) { return $p2 }
    }
    return $p1
}

function Get-Duration {
    param([string]$Path)
    $d = ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 $Path 2>$null
    if ($d) { return [double]$d }
    return 0.0
}

function Stretch-Clip {
    param(
        [string]$SrcPath,
        [double]$TargetSec,
        [string]$OutName
    )
    $out = Join-Path $OutDir $OutName
    $outDir = Split-Path $out -Parent
    New-Item -ItemType Directory -Force -Path $outDir | Out-Null
    if (-not $SrcPath -or -not (Test-Path $SrcPath)) { return $SrcPath }
    $cur = Get-Duration $SrcPath
    if ($cur -ge ($TargetSec - 0.05)) {
        Copy-Item $SrcPath $out -Force
        return $out
    }
    $pad = [math]::Max(0, $TargetSec - $cur)
    $padStr = "{0:F3}" -f $pad
    $targetStr = "{0:F3}" -f $TargetSec
    $filter = "[0:v]fps=30,setpts=PTS-STARTPTS,tpad=stop_mode=clone:stop_duration=$padStr[v];[1:a]atrim=duration=$targetStr,asetpts=PTS-STARTPTS[a]"
    Invoke-Ffmpeg @(
        '-y', '-i', $SrcPath, '-f', 'lavfi', '-i', 'anullsrc=r=48000:cl=mono',
        '-filter_complex', $filter,
        '-map', '[v]', '-map', '[a]',
        '-t', $targetStr,
        '-c:v', 'libx264', '-crf', '18', '-preset', 'fast',
        '-c:a', 'aac', '-b:a', '128k',
        $out
    )
    return $out
}

function Concat-TwoClips {
    param([string]$A, [string]$B, [string]$OutName)
    $out = Join-Path $OutDir $OutName
    if (-not (Test-Path $A)) { return $null }
    if (-not (Test-Path $B)) { return $A }
    $list = Join-Path $OutDir "_tmp_concat.txt"
    @(
        "file '$($A -replace '\\','/')'"
        "file '$($B -replace '\\','/')'"
    ) | Out-File -FilePath $list -Encoding ascii
    Invoke-Ffmpeg @('-y', '-f', 'concat', '-safe', '0', '-i', $list, '-c', 'copy', $out)
    Remove-Item $list -ErrorAction SilentlyContinue
    if (Test-Path $out) { return $out }
    return $A
}

# Build shot 05: link + jungle footage
$shot05 = Resolve-Clip "mirage_link_preview.mp4" "ThreePositionScene.mp4" "ThreePositionPlaceholderScene.mp4"
$jungle = Join-Path $RawDir "mirage_jungle_survive.mp4"
$shot05 = Concat-TwoClips $shot05 $jungle "shot05_positions.mp4"

$segments = @(
    @{ id="01"; file=(Resolve-Clip "mirage_a_explosion_wave.mp4" "IntroHookScene.mp4"); target=30 },
    @{ id="02"; file=(Join-Path $ManimDir "OldVsNewBombScene.mp4"); target=35 },
    @{ id="03"; file=(Join-Path $ManimDir "PatchTimelineScene.mp4"); target=45 },
    @{ id="03b"; file=(Join-Path $ManimDir "SourcePipelineScene.mp4"); target=30 },
    @{ id="04"; file=(Resolve-Clip "mirage_a_debug_wide.mp4" "GameEvidenceScene.mp4"); target=45 },
    @{ id="05"; file=$shot05; target=50 },
    @{ id="06"; file=(Join-Path $ManimDir "MapBakeBFSScene.mp4"); target=55 },
    @{ id="07"; file=(Join-Path $ManimDir "RuntimeLookupScene.mp4"); target=45 },
    @{ id="08"; file=(Join-Path $ManimDir "DamagePreviewHUDScene.mp4"); target=30 },
    @{ id="09"; file=(Join-Path $ManimDir "DamageCurveScene.mp4"); target=30 },
    @{ id="10"; file=(Join-Path $ManimDir "MirageShockwaveDemoScene.mp4"); target=60 },
    @{ id="11"; file=(Resolve-Clip "mirage_a_explosion_wave.mp4" "OutroScene.mp4"); target=25 }
)

$stretchDir = Join-Path $OutDir "stretched"
New-Item -ItemType Directory -Force -Path $stretchDir | Out-Null

$listFile = Join-Path $OutDir "concat_list.txt"
$lines = @()
foreach ($seg in $segments) {
    if (-not $seg.file -or -not (Test-Path $seg.file)) {
        Write-Warning "Missing clip for shot $($seg.id): $($seg.file)"
        continue
    }
    $stretched = Stretch-Clip -SrcPath $seg.file -TargetSec $seg.target -OutName "stretched\shot_$($seg.id).mp4"
    $escaped = $stretched -replace '\\', '/'
    $lines += "file '$escaped'"
}
$lines | Out-File -FilePath $listFile -Encoding ascii

$draft = Join-Path $OutDir "cs2_c4_shockwave_draft.mp4"
$final = Join-Path $OutDir "cs2_c4_shockwave_final.mp4"
$narrOut = $null
$srt = Join-Path $Root "subtitles_zh.srt"
$audio = Join-Path $Root "audio\narration.wav"
if (-not (Test-Path $audio)) {
    $audioSilent = Join-Path $Root "audio\narration_silent.wav"
    if (Test-Path $audioSilent) { $audio = $audioSilent }
}

Write-Host "Concatenating $($lines.Count) segments..."
Invoke-Ffmpeg @('-y', '-f', 'concat', '-safe', '0', '-i', $listFile, '-c', 'copy', $draft)

if (Test-Path $audio) {
    Write-Host "Mixing narration track..."
    $narrOut = Join-Path $OutDir "cs2_c4_with_narration.mp4"
    Invoke-Ffmpeg @('-y', '-i', $draft, '-i', $audio, '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-map', '0:v:0', '-map', '1:a:0', $narrOut)
}

if (Test-Path $srt) {
    Write-Host "Burning subtitles..."
    $srtEsc = ($srt -replace '\\', '/') -replace ':', '\\:'
    $vf = "subtitles=${srtEsc}:force_style='FontName=Microsoft YaHei,FontSize=24'"
    $subSrc = if (Test-Path $narrOut) { $narrOut } else { $draft }
    Invoke-Ffmpeg @('-y', '-i', $subSrc, '-vf', $vf, '-c:v', 'libx264', '-crf', '18', '-preset', 'fast', '-c:a', 'copy', $final)
    if (-not (Test-Path $final)) {
        Write-Warning "Subtitle burn failed; copying draft to final."
        Copy-Item $draft $final -Force
    }
} else {
    Copy-Item $draft $final -Force
}

$dur = ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 $final 2>$null
Write-Host "Done: $final"
if ($dur) { Write-Host "Duration: $([math]::Round([double]$dur,1))s" }
