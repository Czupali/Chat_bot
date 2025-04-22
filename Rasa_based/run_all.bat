
@echo off
echo Starting all servers for the Rasa-based chatbot...

@REM  Aktivaljuk a virtualis kornyezetet
:: call C:\Users\czupp_0buej30\anaconda3\Scripts\activate.bat chat_bot

@REM  Toroljuk a SESSION_LOG_TIMESTAMP erteket a .env fajlbol
echo Updating .env file...
python -c "from dotenv import load_dotenv, set_key; load_dotenv(); set_key('.env', 'SESSION_LOG_TIMESTAMP', '')"

@REM PID fajl inicializálása
echo. > logs\server_pids.txt

@REM  Inditjuk a Rasa szervert egy uj parancssor ablakban, és mentsuk a PID-et
start "Rasa Server" cmd /k "rasa run --enable-api --cors \"*\" --debug & "

@REM Inditjuk az action szervert egy uj parancssor ablakban, es mentsuk a PID-et
start "Action Server" cmd /k "timeout /t 100 & powershell -Command ""(Get-Process -Name python | Where-Object {$_.CommandLine -like '*rasa run*'}).Id >> logs\server_pids.txt; if(!$?) { echo 'Failed to get Rasa PID' >> logs\server_pids.txt }"" & rasa run actions"


@REM Inditjuk a Gradio appot, mentsuk a PID-et, es megnyitjuk a bongeszoben
start "Gradio App" cmd /k "timeout /t 200 & powershell -Command ""(Get-Process -Name python | Where-Object {$_.CommandLine -like '*rasa run*'}).Id >> logs\server_pids.txt; if(!$?) { echo 'Failed to get Rasa PID' >> logs\server_pids.txt }"" & python gradio_app.py"
@REM python -c \"import webbrowser; webbrowser.open('http://localhost:7860')\""

start "Gradio Web" cmd /k "timeout /t 250 & powershell -Command ""(Get-Process -Name python | Where-Object {$_.CommandLine -like '*rasa run*'}).Id >> logs\server_pids.txt; if(!$?) { echo 'Failed to get Rasa PID' >> logs\server_pids.txt }"" & start chrome http://localhost:7860"

echo All servers started! Check the terminal windows for logs.
pause