#!/bin/bash
# Supervisor: single instance (flock) + automatic restart if bot.py crashes.
# Start:  nohup ./run_bot.sh > /dev/null 2>&1 &      Stop:  pkill -f run_bot.sh; pkill -f bot.py
cd "$(dirname "$0")" || exit 1
PY="${PY:-$HOME/virtualenv/repositories/btc-telegram-trader/3.11/bin/python}"
exec 9>.bot.lock
flock -n 9 || { echo "Bot supervisor already running."; exit 1; }
while true; do
  "$PY" bot.py >> bot.log 2>&1
  echo "[$(date '+%F %T')] bot.py exited (code $?), restarting in 15s" >> bot.log
  sleep 15
done
