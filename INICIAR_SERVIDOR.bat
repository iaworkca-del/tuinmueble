@echo off
title Mi Propiedad - Servidor local
cd /d "%~dp0"
echo ============================================
echo   Mi Propiedad - Servidor local
echo.
echo   Espera unos segundos y se abrira el navegador.
echo   Direccion: http://localhost:8000
echo.
echo   Para DETENER el servidor: cierra esta ventana.
echo ============================================
echo.
echo   NOTA: los mensajes sobre "noticias" o "api-key"
echo   NO son un problema. El servidor funciona igual.
echo ============================================
echo.
start "" http://localhost:8000/login
python -m uvicorn main:app --reload --port 8000 --app-dir MiAgente
pause
