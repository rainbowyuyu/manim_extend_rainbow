@echo off
cd /d "%~dp0..\..\.."
if not exist "video_project\cs2_c4\cs2_c4_edit\manim" mkdir "video_project\cs2_c4\cs2_c4_edit\manim"
python -m manim -qh -v WARNING --disable_caching video_project/cs2_c4/manim/mirage.py IntroHookScene OldVsNewBombScene PatchTimelineScene SourcePipelineScene GameEvidenceScene ThreePositionScene MapBakeBFSScene RuntimeLookupScene DamagePreviewHUDScene DamageCurveScene MirageShockwaveScene OutroScene
if errorlevel 1 exit /b 1
xcopy /Y /Q "media\videos\mirage\1080p60\*.mp4" "video_project\cs2_c4\cs2_c4_edit\manim\"
echo Render complete. Run video_project\cs2_c4\cs2_c4_edit\build_video.ps1 to assemble.
