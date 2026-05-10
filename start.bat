@echo off
if not exist .env (
    copy .env.example .env
    echo Created .env - edit it and set OPENAI_API_KEY, then re-run.
    exit /b 1
)
docker compose up --build
