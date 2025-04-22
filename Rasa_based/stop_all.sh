#!/bin/bash
echo "Stopping all servers..."

# Aktivaljuk a virtualis kornyezetet
# source ~/anaconda3/bin/activate chat_bot

# PID-ek beolvasasa és leallitas
while read pid; do
    kill -9 $pid
done < logs/server_pids.txt

# PID fajl torlese
rm logs/server_pids.txt

echo "All servers stopped!"