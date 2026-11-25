@echo off
setlocal
cd /d "%~dp0"
title FLP Prospect - Inicializador
if not exist "backend\.venv\Scripts\python.exe" (
 echo Ambiente virtual nao encontrado em backend\.venv.
 pause
 exit /b 1
)
if not exist "frontend\node_modules\.bin\vite.cmd" (
 echo Dependencias do frontend nao encontradas. Execute npm install na pasta frontend.
 pause
 exit /b 1
)
powershell -NoProfile -Command "try { Invoke-WebRequest 'http://127.0.0.1:5000/api/metricas' -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop | Out-Null; exit 0 } catch { exit 1 }"
if errorlevel 1 start "FLP Prospect - Backend" /min /D "%~dp0backend" "%~dp0backend\.venv\Scripts\python.exe" app.py
powershell -NoProfile -Command "try { Invoke-WebRequest 'http://localhost:5173' -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop | Out-Null; exit 0 } catch { exit 1 }"
if errorlevel 1 start "FLP Prospect - Frontend" /min /D "%~dp0frontend" cmd /k "npm run dev -- --host localhost --port 5173 --strictPort"
echo Iniciando FLP Prospect...
powershell -NoProfile -Command "$urls=@('http://127.0.0.1:5000/api/metricas','http://localhost:5173'); foreach($url in $urls){$ok=$false; for($i=0;$i -lt 30;$i++){try{Invoke-WebRequest $url -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop | Out-Null; $ok=$true; break}catch{Start-Sleep -Seconds 1}}; if(-not $ok){Write-Host ('Servidor nao respondeu: '+$url); exit 1}}"
if errorlevel 1 (
 echo Verifique as janelas do backend e frontend.
 pause
 exit /b 1
)
start "" "http://localhost:5173"
exit /b 0
