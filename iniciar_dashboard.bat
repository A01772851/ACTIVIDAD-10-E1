@echo off
setlocal
cd /d "%~dp0"

python --version >nul 2>&1
if errorlevel 1 (
    echo No se encontro Python. Instalalo desde python.org y marca "Add Python to PATH".
    pause
    exit /b 1
)

echo Instalando librerias necesarias. La primera vez puede tardar unos minutos...
python -m pip install --quiet --disable-pip-version-check -r requirements.txt
if errorlevel 1 (
    echo Fallo la instalacion de librerias.
    pause
    exit /b 1
)

echo Abriendo el dashboard en el navegador...
python -m streamlit run app_streamlit.py
pause
