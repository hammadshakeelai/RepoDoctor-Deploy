"""
RepoDoctor AI — FastAPI Backend
Real-time multi-agent repository analysis with SSE streaming.
"""

import os
import sys
import json
import asyncio
import traceback
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

# Set OpenAI API key
api_key = os.getenv("OPENAI_API_KEY")
if api_key:
    os.environ["OPENAI_API_KEY"] = api_key

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from sse_starlette.sse import EventSourceResponse
from pydantic import BaseModel

from agents import Runner, Agent
from agents.tracing import set_tracing_disabled

# Disable tracing to avoid needing an OpenAI dashboard
set_tracing_disabled(True)

# Import agents
from backend.agents.tools import clone_repo, get_file_tree, read_file, analyze_dependencies, count_lines_by_language, search_code
from backend.agents.mapper import mapper_agent
from backend.agents.storyteller import storyteller_agent
from backend.agents.hacker import hacker_agent
from backend.agents.sre import sre_agent
from backend.agents.fixer import fixer_agent
from backend.agents.quizzer import quizzer_agent


app = FastAPI(
    title="RepoDoctor AI",
    description="Multi-agent repository analysis platform",
    version="1.0.0"
)

# CORS for React frontend
# CORS: wildcard origin + credentials is rejected by browsers per spec.
# We don't use cookies/auth here, so drop credentials and keep wildcard.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AnalyzeRequest(BaseModel):
    github_url: str


def try_parse_json(text: str):
    """Try to parse JSON from text, handling markdown code blocks."""
    text = text.strip()
    # Remove markdown code blocks if present
    if text.startswith("```"):
        lines = text.split("\n")
        # Remove first and last lines (``` markers)
        lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines)
    
    try:
        return json.loads(text)
    except (json.JSONDecodeError, ValueError):
        return text


async def run_agent_pipeline(github_url: str):
    """Run the full agent pipeline and yield SSE events."""
    
    repo_path = None
    results = {}
    
    try:
        # ====== PHASE 1: Clone Repository ======
        yield {
            "event": "agent_start",
            "data": json.dumps({"agent": "cloner", "message": "Cloning repository..."})
        }
        
        import git
        import shutil
        import tempfile
        
        # Clone directly (not via agent tool, for speed)
        github_url_clean = github_url.strip().rstrip("/")
        if github_url_clean.endswith(".git"):
            repo_name = github_url_clean.split("/")[-1][:-4]
        else:
            repo_name = github_url_clean.split("/")[-1]
        
        repo_temp_dir = os.path.join(tempfile.gettempdir(), "repodoctor_repos")
        os.makedirs(repo_temp_dir, exist_ok=True)
        repo_path = os.path.join(repo_temp_dir, repo_name)
        
        if os.path.exists(repo_path):
            shutil.rmtree(repo_path, ignore_errors=True)
        
        git.Repo.clone_from(github_url_clean, repo_path, depth=1)
        
        yield {
            "event": "agent_complete",
            "data": json.dumps({"agent": "cloner", "message": f"Repository cloned successfully", "repo_name": repo_name})
        }
        
        # ====== PHASE 2: Mapper Agent ======
        yield {
            "event": "agent_start",
            "data": json.dumps({"agent": "mapper", "message": "Analyzing architecture, dependencies, and entry points..."})
        }
        
        mapper_input = f"Analyze the repository at this local path: {repo_path}"
        mapper_result = await Runner.run(mapper_agent, input=mapper_input)
        mapper_output = mapper_result.final_output
        results["mapper"] = try_parse_json(mapper_output)
        
        yield {
            "event": "agent_complete",
            "data": json.dumps({"agent": "mapper", "data": results["mapper"]})
        }
        
        # ====== PHASE 3: Parallel Analysis (Storyteller + Hacker + SRE) ======
        yield {
            "event": "agent_start",
            "data": json.dumps({"agent": "storyteller", "message": "Writing codebase narrative..."})
        }
        yield {
            "event": "agent_start",
            "data": json.dumps({"agent": "hacker", "message": "Scanning for security vulnerabilities..."})
        }
        yield {
            "event": "agent_start",
            "data": json.dumps({"agent": "sre", "message": "Analyzing reliability and scaling..."})
        }
        
        mapper_context = json.dumps(results["mapper"]) if isinstance(results["mapper"], dict) else str(results["mapper"])
        
        # Run 3 agents in parallel
        storyteller_task = Runner.run(
            storyteller_agent,
            input=f"Here is the architecture analysis:\n\n{mapper_context}\n\nThe repo is at: {repo_path}\n\nWrite the narrative."
        )
        hacker_task = Runner.run(
            hacker_agent,
            input=f"Here is the architecture analysis:\n\n{mapper_context}\n\nThe repo is at: {repo_path}\n\nPerform a security audit."
        )
        sre_task = Runner.run(
            sre_agent,
            input=f"Here is the architecture analysis:\n\n{mapper_context}\n\nThe repo is at: {repo_path}\n\nPerform a reliability analysis."
        )
        
        storyteller_result, hacker_result, sre_result = await asyncio.gather(
            storyteller_task, hacker_task, sre_task
        )
        
        results["storyteller"] = storyteller_result.final_output
        results["hacker"] = try_parse_json(hacker_result.final_output)
        results["sre"] = try_parse_json(sre_result.final_output)
        
        yield {
            "event": "agent_complete",
            "data": json.dumps({"agent": "storyteller", "data": results["storyteller"]})
        }
        yield {
            "event": "agent_complete",
            "data": json.dumps({"agent": "hacker", "data": results["hacker"]})
        }
        yield {
            "event": "agent_complete",
            "data": json.dumps({"agent": "sre", "data": results["sre"]})
        }
        
        # ====== PHASE 4: Fixer Agent ======
        yield {
            "event": "agent_start",
            "data": json.dumps({"agent": "fixer", "message": "Generating code fixes..."})
        }
        
        hacker_context = json.dumps(results["hacker"]) if isinstance(results["hacker"], dict) else str(results["hacker"])
        sre_context = json.dumps(results["sre"]) if isinstance(results["sre"], dict) else str(results["sre"])
        
        fixer_result = await Runner.run(
            fixer_agent,
            input=f"Architecture:\n{mapper_context}\n\nSecurity Findings:\n{hacker_context}\n\nReliability Findings:\n{sre_context}\n\nThe repo is at: {repo_path}\n\nPropose fixes."
        )
        results["fixer"] = try_parse_json(fixer_result.final_output)
        
        yield {
            "event": "agent_complete",
            "data": json.dumps({"agent": "fixer", "data": results["fixer"]})
        }
        
        # ====== PHASE 5: Quizzer Agent ======
        yield {
            "event": "agent_start",
            "data": json.dumps({"agent": "quizzer", "message": "Creating onboarding quiz..."})
        }
        
        quizzer_result = await Runner.run(
            quizzer_agent,
            input=f"Architecture:\n{mapper_context}\n\nCodebase Narrative:\n{results['storyteller']}\n\nGenerate quiz questions."
        )
        results["quizzer"] = try_parse_json(quizzer_result.final_output)
        
        yield {
            "event": "agent_complete",
            "data": json.dumps({"agent": "quizzer", "data": results["quizzer"]})
        }
        
        # ====== DONE ======
        yield {
            "event": "analysis_done",
            "data": json.dumps({"status": "complete", "repo_url": github_url})
        }
        
    except Exception as e:
        error_msg = f"{type(e).__name__}: {str(e)}"
        print(f"Pipeline error: {error_msg}")
        traceback.print_exc()
        yield {
            "event": "error",
            "data": json.dumps({"error": error_msg})
        }


@app.post("/api/analyze")
async def analyze_repo(request: AnalyzeRequest):
    """Start repository analysis and stream results via SSE."""
    
    async def event_generator():
        async for event in run_agent_pipeline(request.github_url):
            yield event
    
    return EventSourceResponse(event_generator())


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "RepoDoctor AI"}


# ====== Serve built React frontend (single-container deploy) ======
DIST_DIR = Path(__file__).resolve().parent.parent / "frontend_dist"
if DIST_DIR.exists():
    assets_dir = DIST_DIR / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/{full_path:path}")
    async def spa_fallback(full_path: str):
        if full_path.startswith("api/"):
            return JSONResponse({"detail": "Not Found"}, status_code=404)
        candidate = DIST_DIR / full_path
        if full_path and candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(DIST_DIR / "index.html")


# Run with: uvicorn backend.main:app --host 0.0.0.0 --port 8000
# Do NOT run as `python backend/main.py` — local backend/agents/ would
# shadow the openai-agents SDK package on sys.path[0] and crash imports.
