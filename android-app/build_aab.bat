@echo off
set "JAVA_HOME=C:\Users\Ranch\AppData\Local\jdk17\jdk-17.0.10+7"
set "PATH=%JAVA_HOME%\bin;%PATH%"
cd /d "%~dp0"
echo ========================================================
echo BURGOOD ACCESS CONTROL - GOOGLE PLAY .AAB YARATILMOQDA...
echo ========================================================
call gradlew.bat bundleRelease --no-daemon
if %ERRORLEVEL% EQU 0 (
    echo.
    echo [MUVAFFAQIYAT] .AAB Bundle tayyor!
    copy /Y "app\build\outputs\bundle\release\app-release.aab" "..\BurgoodAccessControl.aab"
    echo Fayl saqlandi: BurgoodAccessControl.aab
) else (
    echo.
    echo [XATOLIK] .AAB yaratishda xatolik yuz berdi!
)
pause
