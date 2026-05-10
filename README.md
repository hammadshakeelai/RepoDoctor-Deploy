---
title: RepoDoctor AI
emoji: 🩺
colorFrom: purple
colorTo: blue
sdk: docker
app_port: 7860
pinned: false
license: mit
short_description: 6 AI agents dissect any GitHub repo in real time.
---

# RepoDoctor AI

Multi-agent GitHub repo auditor. Paste a repo URL → 6 AI agents (Mapper, Storyteller, Hacker, SRE, Fixer, Quizzer) stream results in real time.

## How it works

```
GitHub URL
    │
    ▼
FastAPI /api/analyze (Server-Sent Events)
    │
    ├─► Cloner       (git clone --depth 1)
    ├─► Mapper       (architecture, deps, entry points)
    ├─► Storyteller  ┐
    ├─► Hacker       ├─ run in parallel
    ├─► SRE          ┘
    ├─► Fixer        (code patches)
    └─► Quizzer      (onboarding MCQs)
```

## Configuration

This Space requires one secret:

| Secret           | What it does                          |
|------------------|---------------------------------------|
| `OPENAI_API_KEY` | OpenAI key — used by every agent.     |

Set it in **Settings → Variables and secrets → New secret**.

## Stack

- Backend: FastAPI + OpenAI Agents SDK + SSE streaming
- Frontend: React + Vite (built into static, served by FastAPI)
- Single Docker image, port 7860

For local development and self-hosting docs see [`README.local.md`](README.local.md).
