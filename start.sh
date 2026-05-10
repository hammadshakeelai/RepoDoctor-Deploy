#!/usr/bin/env bash
# Quick local start (Linux/macOS/WSL). Windows users: see README.
set -e
if [ ! -f .env ]; then
  cp .env.example .env
  echo "Created .env — edit it and set OPENAI_API_KEY, then re-run." >&2
  exit 1
fi
docker compose up --build
