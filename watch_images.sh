#!/bin/bash
WATCH_DIR="$HOME/Work/PycharmProjects/PythonProject/data/images"
cd "$WATCH_DIR" || exit

inotifywait -m -e create --format "%f" "$WATCH_DIR" | while read -r FILE; do
    EXT="${FILE##*.}"
    TIMESTAMP=$(date +"%Y-%m-%d_%H-%M-%S")
    NEW_NAME="screenshot_${TIMESTAMP}.${EXT}"
    mv "$FILE" "$NEW_NAME"

    cd "$HOME/Work/PycharmProjects/PythonProject" || exit
    git add "data/images/$NEW_NAME"
    git commit -m "Add screenshot: $NEW_NAME" >/dev/null
    echo "✔ Committed $NEW_NAME"
done
