@echo off
setlocal EnableDelayedExpansion

echo.
echo ============================================================
echo   LoopFlow Toolbar Installer
echo ============================================================
echo.

set "ROOT_DIR=%~dp0"
if "%ROOT_DIR:~-1%"=="\" set "ROOT_DIR=%ROOT_DIR:~0,-1%"
set "SRC_DIR=%ROOT_DIR%\Data"
set "RHINO_SCRIPTS=%APPDATA%\McNeel\Rhinoceros\8.0\scripts\LoopFlow"

rem -- Check Data\ subfolder exists --
if not exist "%SRC_DIR%\" (
    echo [ERROR] Cannot find the Data folder:
    echo         %SRC_DIR%\
    echo.
    echo         Expected layout after unzip:
    echo           LoopFlow\install_LoopFlow.bat
    echo           LoopFlow\LoopFlow.rhc
    echo           LoopFlow\Data\*.py
    echo.
    goto :END_FAIL
)

rem -- Check Rhino 8.0 AppData root exists --
if not exist "%APPDATA%\McNeel\Rhinoceros\8.0\" (
    echo [ERROR] Rhino 8.0 settings folder not found:
    echo         %APPDATA%\McNeel\Rhinoceros\8.0\
    echo.
    echo         Please make sure Rhino 8.0 is installed and has been
    echo         launched at least once before running this installer.
    echo.
    goto :END_FAIL
)
echo [1/3] Rhino 8.0 settings folder ... OK

rem -- Create target folder if needed --
if not exist "%RHINO_SCRIPTS%\" (
    mkdir "%RHINO_SCRIPTS%"
    if errorlevel 1 (
        echo [ERROR] Failed to create target folder:
        echo         %RHINO_SCRIPTS%
        goto :END_FAIL
    )
    echo [2/3] Created: %RHINO_SCRIPTS%
) else (
    echo [2/3] Target folder already exists.
)

rem -- Copy .py files --
echo [3/3] Copying Python scripts...
echo.

set "PY_SRC_COUNT=0"
for %%F in ("%SRC_DIR%\*.py") do set /a PY_SRC_COUNT+=1

if %PY_SRC_COUNT%==0 (
    echo [WARN] No .py files found in:
    echo        %SRC_DIR%\
    echo.
    goto :END_FAIL
)

robocopy "%SRC_DIR%" "%RHINO_SCRIPTS%" *.py /NJH /NJS /NDL /NP
if errorlevel 8 (
    echo [ERROR] robocopy failed ^(exit code ^>= 8^).
    goto :END_FAIL
)

set "PY_DST_COUNT=0"
for %%F in ("%RHINO_SCRIPTS%\*.py") do set /a PY_DST_COUNT+=1
echo   Source : %SRC_DIR%
echo   Target : %RHINO_SCRIPTS%
echo   Copied : !PY_DST_COUNT! of !PY_SRC_COUNT! .py files
echo.

rem -- Locate .rhc in the root folder (same level as this BAT) --
set "RHC_FILE="
for %%F in ("%ROOT_DIR%\*.rhc") do set "RHC_FILE=%%F"

if not defined RHC_FILE (
    set "RHC_MSG=.rhc toolbar file not found next to the installer."
) else (
    set "RHC_MSG=Toolbar file: !RHC_FILE!"
)

rem -- Success popup --
powershell -NoProfile -Command "Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.MessageBox]::Show('!PY_DST_COUNT! scripts copied to Rhino scripts folder.' + [char]10 + [char]10 + 'NEXT STEP:' + [char]10 + '  1. Open Rhino 8' + [char]10 + '  2. Drag LoopFlow.rhc (next to this installer) into any Rhino viewport' + [char]10 + '  3. The LoopFlow toolbar will appear', 'LoopFlow Installer', [System.Windows.Forms.MessageBoxButtons]::OK, [System.Windows.Forms.MessageBoxIcon]::Information)"

echo ============================================================
echo   Installation complete.
echo ============================================================
echo.
pause
exit /b 0

:END_FAIL
echo.
echo ============================================================
echo   Installation failed. See messages above.
echo ============================================================
echo.
pause
exit /b 1
