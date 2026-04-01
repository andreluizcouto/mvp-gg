@echo off
REM ──────────────────────────────────────────────────────────
REM build.bat — Gera CoachApp.exe com PyInstaller
REM Requisitos: py -m pip install pyinstaller
REM Nota: PyArmor requer licenca paga para uso com PyInstaller.
REM       Por ora o build usa apenas PyInstaller (bytecode compilado).
REM ──────────────────────────────────────────────────────────

setlocal enabledelayedexpansion

REM Localiza o diretorio Scripts do Python
for /f "usebackq tokens=*" %%i in (`py -c "import sysconfig; print(sysconfig.get_path('scripts'))"`) do set SCRIPTS=%%i
echo Usando Scripts: %SCRIPTS%

echo [1/3] Limpando builds anteriores...
taskkill /f /im CoachApp.exe >nul 2>&1
timeout /t 1 /nobreak >nul
if exist dist rmdir /s /q dist
if exist build rmdir /s /q build

echo [2/3] Empacotando com PyInstaller...
"%SCRIPTS%\pyinstaller" coach.spec --noconfirm --clean

if errorlevel 1 (
    echo ERRO: PyInstaller falhou.
    exit /b 1
)

echo [3/3] Comprimindo e gerando SHA256...
powershell -Command "Start-Sleep 2; Compress-Archive -Path 'dist\CoachApp' -DestinationPath 'dist\CoachApp_v1.0.zip' -Force"
certutil -hashfile dist\CoachApp_v1.0.zip SHA256 | findstr /v "hash" | findstr /v "CertUtil"

echo.
echo Build concluido! Arquivo: dist\CoachApp_v1.0.zip
echo Publicar o hash SHA256 acima na pagina de download.
