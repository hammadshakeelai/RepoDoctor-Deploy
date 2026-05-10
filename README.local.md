# RepoDoctor AI — Deployable

Multi-agent GitHub repo auditor. Paste a repo URL → 6 AI agents (Mapper, Storyteller, Hacker, SRE, Fixer, Quizzer) stream results in real time.

This is a **single-container** packaging of [REPODOC-AI](https://github.com/your/REPODOC-AI). FastAPI backend serves both the API and the built React frontend. One image, one port, one env var.

---

## 1-minute deploy

### Docker (anywhere)

```bash
git clone <this-repo> repodoctor && cd repodoctor
cp .env.example .env          # then edit .env and put your OPENAI_API_KEY
docker compose up --build -d
# open http://localhost:8000
```

### Render / Railway / Fly.io

1. Push this folder to its own GitHub repo.
2. On the platform, create a new service → "Deploy from Dockerfile".
3. Set env var `OPENAI_API_KEY=sk-...`
4. Done. Configs included:
   - `render.yaml` (Render Blueprint)
   - `railway.json` (Railway)
   - `fly.toml` (Fly.io — `flyctl launch --copy-config`)
   - `Procfile` (Heroku — pair with Heroku's container stack)

### Hugging Face Spaces (Docker)

Create a new Space → SDK: Docker → push these files. Add `OPENAI_API_KEY` as a Space secret.

---

## Local dev (no Docker)

Two terminals:

```bash
# 1) backend
python -m venv .venv && . .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r backend/requirements.txt
export OPENAI_API_KEY=sk-...                      # Windows: set OPENAI_API_KEY=...
uvicorn backend.main:app --reload --port 8000
```

```bash
# 2) frontend (proxies /api to backend on :8000)
cd frontend
npm install
npm run dev          # http://localhost:5173
```

---

## How it works

```
GitHub URL
    │
    ▼
┌────────────────────────────────────────────────────┐
│ FastAPI  /api/analyze  (Server-Sent Events stream) │
└────────────────────────────────────────────────────┘
    │
    ├─► Cloner       (git clone --depth 1)
    ├─► Mapper       (architecture, deps, entry points)
    ├─► Storyteller  ┐
    ├─► Hacker       ├─ run in parallel
    ├─► SRE          ┘
    ├─► Fixer        (code patches)
    └─► Quizzer      (onboarding MCQs)
```

- Backend: `backend/main.py` orchestrates the pipeline using the OpenAI Agents SDK.
- Each agent: `backend/agents/*.py` — prompt + tool list, swap models freely.
- Frontend: Vite + React (`frontend/src/App.jsx`) consumes the SSE stream and renders each agent's result as it lands.

---

## Configuration

| Env var          | Default       | What it does                                    |
|------------------|---------------|-------------------------------------------------|
| `OPENAI_API_KEY` | **required**  | OpenAI key — used by every agent.               |
| `PORT`           | `8000`        | Port FastAPI binds to.                          |

---

## Endpoints

| Method | Path             | Purpose                                       |
|--------|------------------|-----------------------------------------------|
| POST   | `/api/analyze`   | Body `{"github_url": "..."}` → SSE stream     |
| GET    | `/api/health`    | `{"status":"healthy"}`                        |
| GET    | `/`              | React SPA (single-container mode)             |

---

## License

Same as upstream. See LICENSE.
