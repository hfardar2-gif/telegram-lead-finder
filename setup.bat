@echo off
setlocal
where py >nul 2>nul
if errorlevel 1 (
  echo Python was not found. Install Python 3.12 or newer from python.org and enable Add Python to PATH.
  exit /b 1
)
for /f "tokens=2" %%V in ('py -3 -c "import sys; print(sys.version_info.major, sys.version_info.minor)"') do set MINOR=%%V
if not exist .venv py -3 -m venv .venv
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt
if not exist .env copy .env.example .env >nul
echo.
echo Setup complete. Edit .env or run: python -m app.setup_wizard
endlocal

