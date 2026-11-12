@echo off
set "JAVA_HOME=C:\Users\Ranch\AppData\Local\jdk17\jdk-17.0.10+7"
set "PATH=%JAVA_HOME%\bin;%PATH%"
cd /d "d:\BurgoodAccsesCantrol\android-app"
call gradlew.bat assembleDebug --no-daemon
