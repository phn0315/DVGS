@echo off
setlocal
cd /d "%~dp0"
set "SOURCE=%~1"
if not defined SOURCE set /p "SOURCE=Original video directory: "
python -m pip install -r requirements.txt
if errorlevel 1 exit /b 1
python generate_showcase.py --source-dir "%SOURCE%" --output . --skip-video
if errorlevel 1 exit /b 1
echo Done. This package uses Bilibili links only.
pause
