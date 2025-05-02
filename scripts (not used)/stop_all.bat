@echo off
echo Stopping all servers...

:: Aktivaljuk a virtualis kornyezetet
@REM call C:\Users\czupp_0buej30\anaconda3\Scripts\activate.bat chat_bot

:: Ellenorizzuk, hogy letezik-e a PID fajl
if not exist logs\server_pids.txt (
    echo No server_pids.txt found. No servers to stop.
    goto :end
)

:: PID-ek beolvasasa és leallitas
for /f "tokens=*" %%i in (logs\server_pids.txt) do (
    if not "%%i"=="" (
        taskkill /PID %%i /F 2>nul || echo Failed to stop process %%i
    )
)

:: PID fajl torlese
del logs\server_pids.txt

:end
echo All servers stopped!
pause