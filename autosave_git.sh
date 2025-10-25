#!/bin/bash
cd ~/Work/PycharmProjects/PythonProject || exit

trap 'echo "$(date): PyCharm closed, final save..."; git add .; git commit -m "Final save before exit $(date)" >/dev/null 2>&1; git push origin main >/dev/null 2>&1; exit 0' SIGTERM SIGINT

while pgrep -f "pycharm" >/dev/null; do
    echo "$(date): Auto-saving..." >> autosave.log
    git add .
    git commit -m "Auto-save: $(date '+%Y-%m-%d %H:%M:%S')" >/dev/null 2>&1
    git push origin main >/dev/null 2>&1
    sleep 300
done

echo "$(date): PyCharm closed, stopping auto-save..." >> autosave.log

