#!/bin/bash
cd ~/Work/PycharmProjects/PythonProject || exit
while true; do
    git add .
    git commit -m "Auto-save: $(date '+%Y-%m-%d %H:%M:%S')" >/dev/null 2>&1
    git push origin main >/dev/null 2>&1
    sleep 300  # wait 5 minutes between pushes
done
