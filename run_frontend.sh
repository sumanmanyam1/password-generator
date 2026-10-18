#!/usr/bin/env bash
# run_frontend.sh — start the PassGen React dev server locally.
set -e
cd "$(dirname "$0")/frontend"

if [ ! -d "node_modules" ]; then
  echo "Installing frontend dependencies…"
  npm install
fi

echo "Starting frontend on http://127.0.0.1:5173 …"
npm run dev
