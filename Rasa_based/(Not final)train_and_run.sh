#!/bin/bash

echo "🔁 Checking if training is needed..."

# Ellenorizzuk, van-e uj tanito adat
rasa data validate

# Ha nincs modell vagy frissebbek az adatok, ujratrainalunk
if [ ! -f models/*.tar.gz ] || [ -n "$(find data domain.yml config.yml -newer models/*.tar.gz)" ]; then
    echo "🚀 Training model..."
    rasa train
else
    echo "✅ Model is up-to-date. No need to retrain."
fi

echo "⚙️  Starting action server..."
gnome-terminal --tab --title="Rasa Actions" -- bash -c "rasa run actions; exec bash"

sleep 3

echo "💬 Starting chatbot shell..."
rasa shell
