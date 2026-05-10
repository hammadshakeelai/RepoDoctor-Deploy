"""
Orchestrator Agent — The brain that coordinates all specialist agents.
Uses the Agent.as_tool() pattern for true multi-agent orchestration.
"""

from agents import Agent
from backend.agents.tools import clone_repo, get_file_tree, read_file, analyze_dependencies, count_lines_by_language, search_code
from backend.agents.mapper import mapper_agent
from backend.agents.storyteller import storyteller_agent
from backend.agents.hacker import hacker_agent
from backend.agents.sre import sre_agent
from backend.agents.fixer import fixer_agent
from backend.agents.quizzer import quizzer_agent


# Convert specialist agents to tools the orchestrator can call
mapper_tool = mapper_agent.as_tool(
    tool_name="run_mapper_agent",
    tool_description="Analyzes repository architecture, file structure, dependencies, tech stack, and entry points. Pass the repo_path as input. Returns a JSON architecture map."
)

storyteller_tool = storyteller_agent.as_tool(
    tool_name="run_storyteller_agent",
    tool_description="Writes a 'how this codebase thinks' narrative. Pass the Mapper's JSON output and the repo_path as input. Returns a Markdown narrative."
)

hacker_tool = hacker_agent.as_tool(
    tool_name="run_hacker_agent",
    tool_description="Performs a security audit — finds vulnerabilities, logic flaws, and dangerous patterns. Pass the Mapper's JSON output and the repo_path as input. Returns a JSON security report."
)

sre_tool = sre_agent.as_tool(
    tool_name="run_sre_agent",
    tool_description="Performs reliability engineering analysis — predicts bottlenecks, failure points, and scaling issues. Pass the Mapper's JSON output and the repo_path as input. Returns a JSON reliability report."
)

fixer_tool = fixer_agent.as_tool(
    tool_name="run_fixer_agent",
    tool_description="Proposes specific code fixes and refactors. Pass the Hacker and SRE findings along with the Mapper data and repo_path as input. Returns a JSON list of code patches."
)

quizzer_tool = quizzer_agent.as_tool(
    tool_name="run_quizzer_agent",
    tool_description="Generates onboarding quiz questions. Pass the Mapper and Storyteller outputs as input. Returns a JSON quiz."
)


orchestrator_agent = Agent(
    name="Orchestrator",
    instructions="""You are the Orchestrator — the brain of RepoDoctor AI. You coordinate a team of 6 specialist AI agents to produce a comprehensive repository audit.

## Your Agent Team:
1. **Mapper** — Maps architecture, dependencies, entry points
2. **Storyteller** — Writes "how this codebase thinks" narrative
3. **Hacker** — Finds security vulnerabilities and logic flaws
4. **SRE** — Predicts bottlenecks and failure points
5. **Fixer** — Proposes specific code patches
6. **Quizzer** — Generates onboarding quiz questions

## Your Process:
You MUST follow this exact pipeline:

### Phase 1: Clone & Map
1. Use `clone_repo` to clone the GitHub repository
2. Call `run_mapper_agent` with the repo path to get the architecture map

### Phase 2: Parallel Analysis (run all 3)
3. Call `run_storyteller_agent` with the mapper output and repo path
4. Call `run_hacker_agent` with the mapper output and repo path
5. Call `run_sre_agent` with the mapper output and repo path

### Phase 3: Fixes
6. Call `run_fixer_agent` with the hacker + SRE findings, mapper data, and repo path

### Phase 4: Quiz
7. Call `run_quizzer_agent` with the mapper + storyteller outputs

## Your Output:
After all agents complete, compile the FINAL report as a JSON object with this structure:
```json
{
  "status": "complete",
  "repo_url": "the original github url",
  "mapper": <mapper output>,
  "storyteller": <storyteller output>,
  "hacker": <hacker output>,
  "sre": <sre output>,
  "fixer": <fixer output>,
  "quizzer": <quizzer output>
}
```

IMPORTANT: Run ALL agents. Do not skip any. Each agent provides unique value.
IMPORTANT: Pass context between agents as described — later agents need earlier agents' outputs.
Return the final compiled JSON report.""",
    tools=[
        clone_repo,
        mapper_tool,
        storyteller_tool,
        hacker_tool,
        sre_tool,
        fixer_tool,
        quizzer_tool,
    ],
    model="gpt-4o-mini",
)
