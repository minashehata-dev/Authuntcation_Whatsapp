@echo off
chcp 65001 > nul
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8

echo ============================================================
echo   WhatsApp OTP Verification System
echo ============================================================
echo.

set PYTHON_EXE=C:\Users\%USERNAME%\AppData\Local\Python\pythoncore-3.14-64\python.exe

if not exist "%PYTHON_EXE%" (
    set PYTHON_EXE=C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python313\python.exe
)

if not exist "%PYTHON_EXE%" (
    set PYTHON_EXE=python
)

echo [*] Python executable: %PYTHON_EXE%
echo [*] Starting services...
echo.

"%PYTHON_EXE%" run_services.py

pause
