@echo off
setlocal
cd /d "%~dp0"
where ffmpeg >nul 2>&1
if errorlevel 1 (
  echo ERROR: FFmpeg is not on PATH. Install FFmpeg and restart Command Prompt.
  pause
  exit /b 1
)
where python >nul 2>&1
if errorlevel 1 (
  echo ERROR: Python 3.11 or later is required.
  pause
  exit /b 1
)
python -m pip install -r requirements.txt
if not exist "work\episode_001\plan.json" python agent.py --sample --output work\episode_001
echo Place Google Flow exports in the clips folder:
echo scene_01.mp4 ... scene_05.mp4
python producer.py --project work\episode_001\plan.json --clips clips --out output
if errorlevel 1 (
  echo ERROR: The video could not be built. Check missing clips and error messages.
) else (
  echo SUCCESS: output\hindi_kids_short.mp4
)
pause
