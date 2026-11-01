@echo off
setlocal EnableExtensions
rem Move to the folder of this file, wherever it is launched from
cd /d "%~dp0"

rem The virtual environment lives outside the project folder on purpose.
rem Windows limits paths to 260 characters and PySide6 has very long file names,
rem so installing inside a deep folder such as Downloads can fail.
set "VENV=%LOCALAPPDATA%\MotoGPAnalyzer\venv"
set "VENV_PY=%VENV%\Scripts\python.exe"
set "INSTALLED=%VENV%\requirements.installed.txt"
set "NOPY_REASON="

rem Last Python 3.12 release with an official Windows installer, 64-bit
set "PY_WINGET_ID=Python.Python.3.12"
set "PY_URL=https://www.python.org/ftp/python/3.12.10/python-3.12.10-amd64.exe"

rem ---- 1) Virtual environment: created only if it does not exist ----
if exist "%VENV_PY%" goto requirements
call :find_python
if not defined PYCMD call :install_python
if not defined PYCMD goto no_python
echo Creating the virtual environment...
%PYCMD% -m venv "%VENV%"
if errorlevel 1 goto venv_failed

:requirements
rem ---- 2) Libraries: installed only if requirements.txt is new or changed ----
fc /b requirements.txt "%INSTALLED%" >nul 2>&1
if not errorlevel 1 goto run_app
echo.
echo Installing the required libraries. This happens only the first time
echo and may take a few minutes: PySide6 is a large download.
echo.
"%VENV_PY%" -m pip install -r requirements.txt
if errorlevel 1 goto pip_failed
copy /y requirements.txt "%INSTALLED%" >nul

:run_app
rem ---- 3) Start the application ----
"%VENV_PY%" src\app\main.py
if errorlevel 1 (
    echo.
    echo The application closed with an error. See the message above.
    pause
)
exit /b 0

:no_python
echo.
echo Python 3.11, 3.12 or 3.13 is required and could not be installed automatically.
if defined NOPY_REASON echo %NOPY_REASON%
echo.
echo You can install Python 3.12 manually from https://www.python.org/downloads/
echo tick "Add python.exe to PATH" in the installer, then run this file again.
pause
exit /b 1

:venv_failed
echo.
echo Could not create the virtual environment.
pause
exit /b 1

:pip_failed
echo.
echo Installation failed. See the error above. Common causes are a missing
echo internet connection or a very long user name. Run this file again to retry.
pause
exit /b 1


rem ======================================================================
rem Looks for Python 3.12, 3.13 or 3.11 and sets PYCMD if it finds one
rem ======================================================================
:find_python
set "PYCMD="
for %%V in (3.12 3.13 3.11) do (
    if not defined PYCMD (
        py -%%V --version >nul 2>&1 && set "PYCMD=py -%%V"
    )
)
rem Also look in the per-user install folders: right after an installation
rem the PATH of this window is not updated yet
if not defined PYCMD if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" set "PYCMD="%LOCALAPPDATA%\Programs\Python\Python312\python.exe""
if not defined PYCMD if exist "%LOCALAPPDATA%\Programs\Python\Python313\python.exe" set "PYCMD="%LOCALAPPDATA%\Programs\Python\Python313\python.exe""
if not defined PYCMD if exist "%LOCALAPPDATA%\Programs\Python\Python311\python.exe" set "PYCMD="%LOCALAPPDATA%\Programs\Python\Python311\python.exe""
exit /b 0


rem ======================================================================
rem Offers to install Python 3.12 for the current user, no admin needed
rem ======================================================================
:install_python
echo.
echo Python 3.11, 3.12 or 3.13 was not found on this computer.
choice /c YN /m "Install Python 3.12 now"
if errorlevel 2 exit /b 0

where winget >nul 2>&1
if errorlevel 1 goto download_python
echo.
echo Installing Python 3.12 with winget...
winget install --id %PY_WINGET_ID% --exact --scope user --silent --accept-package-agreements --accept-source-agreements
call :find_python
if defined PYCMD exit /b 0
echo winget could not install Python. Trying the direct download...

:download_python
echo.
rem Do not start a second installer while one from a previous attempt is still running
tasklist /fi "imagename eq python-3.12.10-amd64.exe" 2>nul | find /i "python-3.12.10-amd64.exe" >nul
if not errorlevel 1 goto installer_running

set "INSTALLER=%TEMP%\python-3.12.10-amd64.exe"
del "%INSTALLER%" >nul 2>&1
echo Downloading the official installer from python.org...
curl.exe -L --fail --show-error --progress-bar -o "%INSTALLER%" "%PY_URL%"
if errorlevel 1 goto download_failed

rem Run the installer only if it is signed by the Python Software Foundation
powershell -NoProfile -Command "$s = Get-AuthenticodeSignature -FilePath '%INSTALLER%'; if ($s.Status -eq 'Valid' -and $s.SignerCertificate.Subject -like '*Python Software Foundation*') { exit 0 } else { exit 1 }"
if errorlevel 1 goto signature_failed

echo.
echo Installing Python. A small progress window will appear. This can take
echo a few minutes: please do not close this window.
start /wait "" "%INSTALLER%" /passive InstallAllUsers=0 PrependPath=1 Include_launcher=1 Include_test=0 /log "%TEMP%\python-install.log"
set "INSTALL_EXIT=%errorlevel%"
del "%INSTALLER%" >nul 2>&1
call :find_python
if defined PYCMD exit /b 0
set "NOPY_REASON=The installer finished with code %INSTALL_EXIT% but Python was not found. Log file: %TEMP%\python-install.log"
exit /b 0

:installer_running
set "NOPY_REASON=The Python installer from a previous attempt is still running. Wait until it finishes, then run this file again."
exit /b 0

:download_failed
set "NOPY_REASON=The download failed. Check your internet connection."
exit /b 0

:signature_failed
del "%INSTALLER%" >nul 2>&1
set "NOPY_REASON=The installer signature could not be verified, so it was not run."
exit /b 0