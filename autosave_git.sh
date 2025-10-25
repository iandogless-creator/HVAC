#!/bin/bash
cd ~/Work/PycharmProjects/PythonProject || exit
LOGFILE="$HOME/Work/PycharmProjects/PythonProject/autosave.log"
while true; do
    echo "$(date): Auto-saving..." >> "$LOGFILE"
    git add . >> "$LOGFILE" 2>&1
    git commit -m "Auto-save: $(date '+%Y-%m-%d %H:%M:%S')" >> "$LOGFILE" 2>&1
    git push origin main >> "$LOGFILE" 2>&1
    sleep 300
done
