#!/usr/bin/env bash
# run_backend.sh — start the PassGen Flask API locally.
set -e
cd "$(dirname "$0")/backend"

if [ ! -d ".venv" ]; then
  echo "Creating virtual environment…"
  python -m venv .venv
fi

# shellcheck disable=SC1091
. .venv/bin/activate
pip install --quiet -r requirements.txt

echo "Starting API on http://127.0.0.1:5000 …"
python api/app.py
