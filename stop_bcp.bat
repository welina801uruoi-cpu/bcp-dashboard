@echo off
taskkill /F /IM ngrok.exe >nul 2>&1
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":5000" ^| findstr "LISTENING"') do taskkill /F /T /PID %%a >nul 2>&1
taskkill /F /FI "WINDOWTITLE eq BCP Backend Server*" /T >nul 2>&1
ping 127.0.0.1 -n 2 >nul
exit
