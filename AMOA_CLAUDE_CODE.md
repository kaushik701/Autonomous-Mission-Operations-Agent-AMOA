# AMOA — Claude Code Structure

**Version:** 3 (final)
**Date:** May 19, 2026
**Supersedes:** W0 addendum

This document defines the Claude Code repo structure for AMOA. You create these files Saturday May 23 as part of W0.

---

## 1. Repository Layout

Two repos. The main one created in W0, the MCP one created in W6.

### Repo A: `amoa` (private until W7)

```
amoa/
├── CLAUDE.md                          # Project memory for Claude Code (Section 2)
├── README.md                          # Public-facing, grows W5→W7
├── REPORT.md                          # Technical writeup, grows weekly
├── IDEAS_PARKING_LOT.md               # Scope-creep parking; ideas you don't act on
├── Makefile                           # dev, demo, eval, test, lint
├── pyproject.toml
├── .env.example                       # Committed; never commit .env itself
├── .gitignore
├── docs/
│   ├── architecture.md                # System diagram, state schema, stub in W0
│   └── decisions/                     # ADRs, one file per decision
│       ├── 0001-stack-choices.md      # Written W0
│       ├── 0002-provider-strategy.md  # Written W1
│       ├── 0003-data-layer.md         # Written W2
│       ├── 0004-baseline-choice.md    # Written W2
│       ├── 0005-snapshot-testing.md   # Written W3
│       ├── 0006-supervisor-design.md  # Written W4
│       └── 0007-mcp-separation.md     # Written W6
├── .claude/
│   └── settings.json                  # Per-project Claude Code config
├── src/amoa/
│   ├── __init__.py
│   ├── config.py                      # Pydantic Settings, .env loader
│   ├── llm.py                         # Provider abstraction (W1)
│   ├── state.py                       # LangGraph state, grows weekly
│   ├── graph.py                       # The LangGraph itself
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── safety_pilot.py            # W1
│   │   ├── health_guard.py            # W2
│   │   ├── payload_scientist.py       # W3
│   │   └── supervisor.py              # W4
│   ├── data/
│   │   ├── spacetrack_client.py       # W1, refactored W6 into MCP
│   │   ├── esa_loader.py              # W2
│   │   └── sentinel_loader.py         # W3
│   ├── baselines/
│   │   └── isolation_forest.py        # W2
│   ├── eval/
│   │   ├── harness.py                 # W5 consolidation
│   │   ├── metrics.py                 # Bootstrap CIs, F1, latency
│   │   ├── failures.jsonl             # Append-only failure log, grows weekly
│   │   └── results/                   # Per-run outputs, gitignored except .gitkeep
│   └── ui/
│       └── streamlit_app.py           # W5
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── fixtures/
│   │   ├── cdms/                      # Mocked CDM JSON
│   │   ├── telemetry/                 # ESA slice fixtures
│   │   └── imagery/                   # Curated Sentinel-2 scenes
│   ├── snapshots/                     # syrupy snapshots, W3 onward
│   └── test_*.py
├── notebooks/                         # Exploration only; gitignored body
└── data/                              # Raw datasets, gitignored
```

### Repo B: `spacetrack-mcp` (public from W6)

Created W6, not W0. Layout shown in `AMOA_PLAN.md` Section 6 W6.

## 2. CLAUDE.md Template (root of `amoa/`)

This file is what Claude Code reads at the start of every session. Keep it under 200 lines. Update the "Current week" line every Monday morning.

```markdown
# AMOA — Claude Code Project Memory

## Project

AMOA (Autonomous Mission Operations Agent) — a multi-agent LLM system
coordinating satellite mission operations under a LangGraph supervisor.
Three specialized agents:

- **Safety Pilot** (Claude Sonnet → Groq Llama 3.3 June 17) — collision avoidance
- **Health Guard** (Gemini 2.5 Flash-Lite) — telemetry anomaly detection
- **Payload Scientist** (Gemini 2.5 Flash Vision) — Sentinel-2 imagery analysis

Plus a Supervisor (LangGraph Send fan-out) and a hybrid rule+LLM Conflict
Resolver. Local digital-twin simulation. Not flight software. Portfolio
project demonstrating agent-system harness engineering.

## Constraints

- 6 GB RAM Windows laptop — cloud APIs handle all reasoning
- 10.5 hr/week budget, 8 weeks May 23 – July 12, 2026
- Free-tier API quotas; $40 Anthropic cap (expires June 16)
- Async everywhere; never block the event loop
- Pydantic v2 for every cross-module boundary
- Medium harness approach: each week adds a small harness deliverable

## Stack

Python 3.11+, `uv`, LangGraph, Pydantic v2, `httpx`, `spacetrack`,
`scikit-learn`, `scipy.stats`, `anthropic`, `google-generativeai`, `groq`,
`mcp` (W6), Streamlit, SQLModel + SQLite, `diskcache`, `syrupy`, `ruff`,
`pytest`, `pytest-asyncio`.

## Code style

- Async functions for any I/O. `asyncio.gather` for parallel agent calls.
- Pydantic models at every function boundary that crosses a module.
- Tests in `tests/`, fixtures in `tests/fixtures/`, snapshots in `tests/snapshots/`.
- One agent = one file in `src/amoa/agents/`.
- Prompts live next to the agent that uses them.
- All LLM calls go through `src/amoa/llm.py:structured_completion`. Agents
  never import `anthropic`, `groq`, or `google.generativeai` directly.
- Failures get categorized and appended to `src/amoa/eval/failures.jsonl`.
- No premature abstraction. Three uses before refactoring.

## How to work with me (Claude Code instructions)

- I am a new grad targeting AI/ML engineering roles. Every line must be
  defensible in interviews — I need to understand it, not just copy it.
- Push back on bad ideas. Don't write code I haven't sketched first.
- When I ask "just write it," refuse and ask me to outline the approach.
- Prefer small reviewable edits over large generated files.
- Surface trade-offs; if there are two reasonable ways, say so and ask.
- Errors and edge cases get explicit handling, not silent swallowing.
- If a file is becoming a mess, say so and propose a refactor.

## Active week

- **Current week:** W0 (May 23) — scaffolding
- **Next milestone:** W1 — Safety Pilot foundation + `llm.py`

## Reference docs

- `AMOA_PLAN.md` — master plan, 8-week schedule, decisions
- `docs/architecture.md` — system diagram + state schema
- `docs/decisions/` — ADRs, one per decision
- `REPORT.md` — technical writeup, grows weekly toward 2500 words

## Gotchas

- Space-Track cookie auth expires after ~2 hours; `spacetrack` lib handles
  refresh, don't bypass it.
- Space-Track rate limits: 30 req/min, 300 req/hr. Library throttles; don't disable.
- ESA Anomaly Dataset is 12 GB total. Use Mission 1 only, time-windowed.
- Gemini free tier RPM caps are tight. Cache aggressively in dev.
- LangGraph `Send` requires destination node to accept the payload shape,
  not full state. Mismatch → silent fan-out failure.
- 6 GB RAM means closing VS Code/Antigravity when running Streamlit + agents
  full-tilt. Watch the page file.
- All LLM calls through `llm.py`. Direct SDK imports in agent files = bug.
- Anthropic credit expires June 16. Plan to flip `AMOA_LLM_PROVIDER=groq`
  in `.env` on Wed June 17. See ADR-0002.
- Snapshot tests (`syrupy`) lock expected behavior. If a test fails after a
  prompt change, that's the signal — review the diff, decide intentional or
  regression, update snapshot only if intentional.

## Harness discipline

Every week has a harness deliverable. Skipping it once is a warning. Skipping
twice is a sign to pause and recalibrate. See `AMOA_PLAN.md` Section 3 for
the weekly harness table.
```

## 3. `.claude/settings.json`

Per-project Claude Code config. The `deny` block stops accidental reads of `.env` and dangerous commands without explicit override.

```json
{
  "description": "AMOA — Autonomous Mission Operations Agent",
  "permissions": {
    "allow": [
      "Read(*.py)",
      "Read(*.md)",
      "Read(*.toml)",
      "Read(*.json)",
      "Read(tests/**)",
      "Edit(src/**)",
      "Edit(tests/**)",
      "Edit(docs/**)",
      "Edit(*.md)",
      "Bash(uv:*)",
      "Bash(pytest:*)",
      "Bash(ruff:*)",
      "Bash(make:*)",
      "Bash(git status)",
      "Bash(git diff*)",
      "Bash(git log*)",
      "Bash(git add*)",
      "Bash(git commit*)"
    ],
    "deny": [
      "Bash(rm -rf*)",
      "Bash(git push*)",
      "Bash(git reset --hard*)",
      "Read(.env)",
      "Edit(.env)"
    ]
  }
}
```

## 4. `docs/architecture.md` (initial stub for W0)

```markdown
# AMOA — Architecture

## System Overview

```
[User] → [Streamlit UI] → [LangGraph Supervisor]
                              │
                  ┌───────────┼───────────┐
                  ▼           ▼           ▼
            [Safety Pilot] [Health Guard] [Payload Scientist]
                  │           │           │
                  └───────────┼───────────┘
                              ▼
                       [Conflict Resolver]
                              ▼
                          [MissionState]
```

Mermaid diagram lands in W4 when supervisor exists.

## State Schema

`MissionState` (Pydantic) accumulates outputs across the graph.

By week:
- W0: `messages: list[HelloMessage]` (placeholder)
- W1: + `safety_assessment: SafetyAssessment | None`
- W2: + `health_assessment: HealthAssessment | None`
- W3: + `payload_assessment: PayloadAssessment | None`
- W4: + `supervisor_decision`, `failure_log: list[FailureEvent]`

## Provider Routing

All LLM calls go through `src/amoa/llm.py:structured_completion`. Provider
selected by `AMOA_LLM_PROVIDER` env var. See ADR-0002.

## Data Sources

- Space-Track (TLEs, CDMs) → Safety Pilot
- ESA Anomaly Dataset, Mission 1 → Health Guard
- Sentinel-2 via Copernicus STAC → Payload Scientist

## Observability

LangSmith tracing on every agent call. Project: `amoa`. Failures also
logged to `src/amoa/eval/failures.jsonl` for offline analysis.

## Deployment

Local only. `make demo` boots Streamlit at localhost:8501. No cloud deploy
this iteration. Recorded walkthrough is the shareable artifact.
```

## 5. ADR-0001 Content (write Saturday in W0)

`docs/decisions/0001-stack-choices.md`:

```markdown
# ADR-0001: Core Stack Choices

**Date:** 2026-05-23
**Status:** Accepted
**Week:** W0

## Context

Building a multi-agent satellite mission system in 8 weeks at 10.5 hr/week.
Pick foundation libraries that don't fight each other and that I can defend
in interviews.

## Decision

- **LangGraph** for orchestration (over CrewAI, AutoGen, raw asyncio)
- **Pydantic v2** for schemas (over dataclasses, attrs)
- **uv** for package management (over poetry, pip-tools)
- **Anthropic, Google, Groq** SDKs directly (no LangChain wrapper layers)
- **SQLite via SQLModel** (over JSON files, Postgres)
- **Streamlit** for UI (over FastAPI + React, Gradio)
- **LangSmith** for tracing (over OpenTelemetry + Phoenix)
- **syrupy** for snapshot testing (over hand-rolled fixtures)

## Rationale

- LangGraph models state machines explicitly; CrewAI hides too much coordination
  for an interview-defensible project.
- Pydantic enforces schemas at function boundaries; catches LLM hallucination
  shapes before they reach downstream agents.
- `uv` is ~10x faster than pip and simpler than poetry's lockfile semantics.
- Direct SDKs are easier to debug than wrapper abstractions; also makes
  provider swap (ADR-0002) cleaner.
- SQLite produces a real schema for interview discussion; JSON files don't.
- Streamlit eliminates a week of front-end work for a demo-only UI.
- LangSmith integrates natively with LangChain ecosystem.
- syrupy gives snapshot diffs as part of pytest output, no separate framework.

## Trade-offs Accepted

- LangGraph couples to LangChain ecosystem. If LangChain pivots, supervisor
  needs rewrite. Acceptable; agent logic stays portable.
- LangSmith is closed-source. Free tier is sufficient.
- Streamlit is not production-grade UI. Acceptable; demo only.

## Alternatives Considered

- **CrewAI:** simpler API but hides coordination logic.
- **AutoGen:** Microsoft-backed but heavier and less LangGraph-native.
- **Phoenix (Arize) for tracing:** more flexible but more setup time.
- **OpenTelemetry directly:** correct but expensive to set up in a portfolio
  timeline.
```

## 6. ADR-0002 Content (write Saturday in W0, after ADR-0001)

`docs/decisions/0002-provider-strategy.md`:

```markdown
# ADR-0002: LLM Provider Strategy Under Credit Constraint

**Date:** 2026-05-23
**Status:** Accepted
**Week:** W0

## Context

Anthropic API access expires June 16, 2026 (W4 of project). Plan ends
July 12. Need a strategy that uses Claude where it matters most and ships
on a sustainable provider mix.

## Decision

- Safety Pilot and Conflict Resolver use Claude Sonnet through W4 Tuesday.
- Health Guard uses Gemini 2.5 Flash-Lite throughout.
- Payload Scientist uses Gemini 2.5 Flash Vision throughout.
- W4 Wednesday (June 17) flips `AMOA_LLM_PROVIDER=groq` in `.env`. Safety
  Pilot and Resolver migrate to Groq Llama 3.3 70B.
- W5 Monday runs full eval suite on Groq; comparison to last Claude run
  documented in REPORT.md.
- Shipped (W7) default uses Groq. Claude available behind config flag for
  users with their own key.

## Implementation

A single `llm.py` module exposes `structured_completion(system, user, schema,
*, provider=None, ...)` with provider as env-var-driven default and per-call
override. Agents are provider-agnostic. They never import `anthropic` or
`groq` directly. Per-call override enables paired comparison in eval.

## Rationale

- Claude has strongest structured-output adherence; using it in W1–W4
  reduces friction during architecturally demanding weeks.
- The forced swap turns a constraint into a comparative-eval exercise, which
  strengthens the interview narrative.
- Gemini's free tier is stable and generous; no reason to swap mid-project.
- Groq Llama 3.3 70B is free-tier-friendly and has fast TTFT, natural
  fallback for Safety Pilot's real-time framing.

## Trade-offs

- Claude credit is finite ($49.35 balance, $40 hard cap). Mitigated via
  diskcache, conservative max_tokens, Claude-only-where-needed.
- Llama 3.3 may need prompt re-tuning for JSON adherence post-swap.
  Time budgeted W4 Wednesday-Thursday.
- "Best demo" version may differ from "default config" version. Documented
  in README.
```

## 7. `.gitignore`

```
# Python
__pycache__/
*.pyc
.venv/
.uv/
*.egg-info/

# Environment
.env
.env.local

# Data — never commit raw datasets
data/
!data/.gitkeep

# Caches
.diskcache/
.cache/
.pytest_cache/
.ruff_cache/

# Editor
.vscode/
.idea/

# OS
.DS_Store
Thumbs.db

# Notebooks
.ipynb_checkpoints/
notebooks/*.ipynb

# LangSmith
.langsmith/

# Eval outputs (results regenerated per run)
src/amoa/eval/results/*.json
!src/amoa/eval/results/.gitkeep

# Claude Code sessions
.claude/sessions/
.claude/logs/
!.claude/settings.json

# DO commit failures.jsonl — it's the growing failure-mode log
```

## 8. `Makefile`

```makefile
.PHONY: dev demo eval test lint format

dev:
	uv run streamlit run src/amoa/ui/streamlit_app.py

demo:
	uv run python -m amoa.graph

eval:
	uv run python -m amoa.eval.harness

test:
	uv run pytest -v

lint:
	uv run ruff check src/ tests/
	uv run ruff format --check src/ tests/

format:
	uv run ruff format src/ tests/
	uv run ruff check --fix src/ tests/
```

On Windows without `make`, run the commands directly:
- `uv run streamlit run src/amoa/ui/streamlit_app.py`
- `uv run python -m amoa.graph`
- `uv run pytest -v`

## 9. What's NOT in the Structure

Skip these from generic Claude Code templates — they're cargo cult for a project this size:

- `.claude/skills/` — use gstack's installed skills; don't build project-specific ones
- `.claude/hooks/` — adds friction without ROI for a solo 8-week project
- `tools/scripts/` — empty folder until W3+; add when you have 3+ scripts
- `tools/prompts/` — prompts live next to the agents that use them
- Per-module `CLAUDE.md` files (e.g. `src/api/CLAUDE.md`) — root CLAUDE.md is enough at this scale
- `docs/runbooks/` — not deploying to production

When in doubt, fewer files. Add structure when a real need emerges (3+ uses), not pre-emptively.

---

That's the full repo structure. `AMOA_W0.md` walks you through creating these files Saturday morning.
