@echo off
cd /d "%~dp0"
python -m yty_manim.tools.map_editor video_project\custom_maps\de_mirage_editable
if errorlevel 1 pause
