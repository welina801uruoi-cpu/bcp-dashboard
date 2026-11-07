@echo off
cd /d "%~dp0"

taskkill /F /IM ngrok.exe >nul 2>&1
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":5000" ^| findstr "LISTENING"') do taskkill /F /T /PID %%a >nul 2>&1
taskkill /F /FI "WINDOWTITLE eq BCP Backend Server*" /T >nul 2>&1
ping 127.0.0.1 -n 2 >nul

start "BCP Backend Server" cmd /k python backend_server.py
ping 127.0.0.1 -n 4 >nul
start "ngrok" cmd /k ngrok http 127.0.0.1:5000

exit