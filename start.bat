@echo off
cd /d "%~dp0"

echo Starting backend on port 8080...
start "Stock Hub Backend" cmd /c ".venv\Scripts\python.exe -m src.main serve --port 8080"

echo Starting frontend on port 3000...
start "Stock Hub Frontend" cmd /c "cd frontend && npm run dev"

echo.
echo Backend:  http://localhost:8080
echo Frontend: http://localhost:3000
echo.
echo Press any key to stop both services...
pause > nul

taskkill /FI "WindowTitle eq Stock Hub Backend*" /F > nul 2>&1
taskkill /FI "WindowTitle eq Stock Hub Frontend*" /F > nul 2>&1
echo Services stopped.
