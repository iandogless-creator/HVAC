#!/bin/bash
# Auto-commit & push script for HVAC project

# Go to project root
cd "$(dirname "$0")"

# Stage all tracked files (respects .gitignore)
git add .

# Commit with timestamped message
git commit -m "Auto-commit: $(date '+%Y-%m-%d %H:%M:%S')" || echo "No changes to commit"

# Push to remote
git push origin main
