@echo off
chcp 65001 >nul
title Burgood Access Control - O'rnatish Ustasi
color 0b

echo ========================================================
echo    BURGOOD ACCESS CONTROL - WINDOWS O'RNATISH USTASI
echo ========================================================
echo.
echo [1/3] Dastur fayllari tayyorlanmoqda...
set TARGET_DIR=%~dp0..
set EXE_PATH=%TARGET_DIR%\dist\BurgoodAccessControl\BurgoodAccessControl.exe
set ICO_PATH=%TARGET_DIR%\frontend\public\app_icon.ico

if not exist "%EXE_PATH%" (
    echo [XATO] %EXE_PATH% topilmadi!
    pause
    exit /b
)

echo [2/3] Ish stoliga (Desktop) yorliq (Shortcut) yaratilmoqda...
powershell -Command "$WshShell = New-Object -ComObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut([Environment]::GetFolderPath('Desktop') + '\Burgood Access Control.lnk'); $Shortcut.TargetPath = '%EXE_PATH%'; $Shortcut.WorkingDirectory = '%TARGET_DIR%'; $Shortcut.IconLocation = '%ICO_PATH%'; $Shortcut.Description = 'Burgood Access Control - Face ID & Davomat'; $Shortcut.Save()"

echo [3/3] Windows Brandmauer (Firewall) ruxsati tekshirilmoqda...
netsh advfirewall firewall add rule name="Burgood Access Control Server" dir=in action=allow protocol=TCP localport=8000 profile=any >nul 2>&1

echo.
echo ========================================================
echo  ✅ O'RNATISH MUVAFFAQIYATLI YAKUNLANDI!
echo  Ish stolida "Burgood Access Control" yorlig'i paydo bo'ldi.
echo ========================================================
echo.
echo Dasturni hoziroq ishga tushirish uchun ixtiyoriy tugmani bosing...
pause >nul

start "" "%EXE_PATH%"
exit
