@echo off
REM Builds EffortEstimator.exe - run this on Windows (double-click)
cd /d "%~dp0"
echo Installing build tools...
python -m pip install --upgrade pyinstaller openpyxl
if errorlevel 1 goto error
echo Building EXE...
python -m PyInstaller --noconfirm --clean --onefile --windowed --name "EffortEstimator" main.py
if errorlevel 1 goto error
echo.
echo Done! Your EXE is here: %~dp0dist\EffortEstimator.exe
pause
exit /b 0
:error
echo.
echo Build failed - see the messages above.
pause
exit /b 1
