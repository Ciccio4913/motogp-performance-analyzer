@echo off
setlocal
cd /d "%~dp0"

set "VENV=.venv"
set "VENV_PY=%VENV%\Scripts\python.exe"
set "INSTALLED=%VENV%\requirements.installed.txt"

if not exist "%VENV_PY%" (
    set "PYCMD="
    for %%V in (3.12 3.13 3.11) do (
        if not defined PYCMD (
            py -%%V --version >nul 2>&1 && set "PYCMD=py -%%V"
        )
    )
    if not defined PYCMD (
        echo Python 3.11, 3.12 or 3.13 was not found.
        echo Install Python 3.12 from https://www.python.org/downloads/
        echo and tick "Add python.exe to PATH" in the installer, then run this file again.
        pause
        exit /b 1
    )
    echo Creating the virtual environment with %PYCMD% ...
    %PYCMD% -m venv "%VENV%"
    if errorlevel 1 (
        echo Could not create the virtual environment.
        pause
        exit /b 1
    )
)

fc /b requirements.txt "%INSTALLED%" >nul 2>&1
if errorlevel 1 (
    echo.
    echo Installing the required libraries. This happens only the first time
    echo and may take a few minutes: PySide6 is a large download.
    echo.
    "%VENV_PY%" -m pip install -r requirements.txt
    if errorlevel 1 (
        echo.
        echo Installation failed. Check your internet connection and run this file again.
        pause
        exit /b 1
    )
    copy /y requirements.txt "%INSTALLED%" >nul
)

"%VENV_PY%" src\app\main.py
if errorlevel 1 (
    echo.
    echo The application closed with an error. See the message above.
    pause
)
endlocal