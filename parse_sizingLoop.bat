@echo off
setlocal ENABLEEXTENSIONS DISABLEDELAYEDEXPANSION
goto main

:SetFromReg
FOR /F "tokens=2,*" %%A IN ('REG query "%~1" /v "%~2"^|find /I "REG_"') DO (
    call set %~3=%%B
)
goto :EOF

:GetRegEnv
FOR /F %%A IN ('REG query "%~1" /s^|find /I "REG_"') DO (
    if /I not "%%~A"=="Path" call :SetFromReg "%~1" "%%~A" "%%~A"
)
goto :EOF

:InheritOrDelete
for %%A in (save_TEMP Path SystemRoot SystemDrive ProgramFiles CommonProgramFiles ALLUSERSPROFILE COMPUTERNAME LOGONSERVER USERNAME USERDOMAIN HOMEDRIVE HOMEPATH USERPROFILE APPDATA) do if /I "%%~A"=="%~1" goto :EOF
set %~1=
goto :EOF

:main
REM Save temp
set save_TEMP=%temp%
if not defined save_TEMP set save_TEMP=%tmp%

for /F "delims==" %%A in ('set') do call :InheritOrDelete "%%~A"
call :GetRegEnv "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Environment"
call :GetRegEnv "HKCU\Environment"

REM Special handling for Path
call :SetFromReg "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Environment" Path Path
setlocal
set u=
call :SetFromReg "HKCU\Environment" Path u
endlocal&if not "%Path%"=="" if not "%u%"=="" set Path=%Path%;%u%

REM Restore TEMP/TMP
set TEMP=%save_TEMP%
set save_TEMP=
set TMP=%TEMP%


REM no errors thrown from this if python fails at any point
REM ensure that correct python gets called
REM use catcher.py to provide error handling to main.py
REM use main.py as entry into your python 3
start /w /MIN cmd /c "C:\Python27\python.exe main_sizingLoop.py"
