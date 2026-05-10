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

## One-click deploy

> Replace `YOUR_GH_USER/YOUR_REPO` after pushing this code to GitHub.

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/YOUR_GH_USER/YOUR_REPO)
[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/new/template?template=https%3A%2F%2Fgithub.com%2FYOUR_GH_USER%2FYOUR_REPO)
[![Open in HF Spaces](https://huggingface.co/datasets/huggingface/badges/resolve/main/deploy-on-spaces-md.svg)](https://huggingface.co/new-space?template=YOUR_HF_USER/YOUR_HF_SPACE)

Each button takes you to the platform; you only set `OPENAI_API_KEY` and click deploy.

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

## Required secret

| Env var          | What it does                          |
|------------------|---------------------------------------|
| `OPENAI_API_KEY` | OpenAI key — used by every agent.     |

## Stack

- Backend: FastAPI + OpenAI Agents SDK + SSE streaming
- Frontend: React + Vite (built static, served by FastAPI)
- Single Docker image, port 7860

## Local dev / self-host

See [`README.local.md`](README.local.md) and [`DEPLOY_HF.md`](DEPLOY_HF.md).
