
### Mivel a fejlesztest windows operacios rendszeren vegzem igy nem tudom,
### hogy linuxon megfeleloen mukodik e

#!/bin/bash
echo "Starting all servers for the Rasa-based chatbot..."

# Aktivaljuk a virtualis környezetet
# source ~/anaconda3/bin/activate chat_bot

# Toroljuk a SESSION_LOG_TIMESTAMP erteket a .env fajlbol
echo "Updating .env file..."
python3 -c "from dotenv import load_dotenv, set_key; load_dotenv(); set_key('.env', 'SESSION_LOG_TIMESTAMP', '')"

# PID fajl inicializalasa
: > logs/server_pids.txt

# Inditjuk a Rasa szervert hattwrben, és mentsük a PID-et
rasa run --enable-api --cors "*" --debug &
echo $! >> logs/server_pids.txt
RASA_PID=$!
echo "Rasa server started (PID: $RASA_PID)"

# Varunk 5 masodpercet
sleep 5

# Inditjuk az action szervert hatterben, es mentsuk a PID-et
rasa run actions &
echo $! >> logs/server_pids.txt
ACTION_PID=$!
echo "Action server started (PID: $ACTION_PID)"

# Varunk 5 masodpercet
sleep 5

# Inditjuk a Gradio appot, mentsuk a PID-et, es megnyitjuk a bogeszoben
python3 gradio_app.py &
echo $! >> logs/server_pids.txt
GRADIO_PID=$!
echo "Gradio app started (PID: $GRADIO_PID)"
# python3 -c "import webbrowser; webbrowser.open('http://localhost:7860')"
google-chrome http://localhost:7860 &

echo "All servers started! Use 'kill $RASA_PID $ACTION_PID $GRADIO_PID' to stop them."
wait