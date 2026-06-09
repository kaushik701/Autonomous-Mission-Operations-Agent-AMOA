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

## Current status

**Completed:**
- `llm.py` provider abstraction (Groq/Gemini), retry-with-correction, failure logging
- Safety Pilot, Health Guard, Payload Scientist agents — all wired into LangGraph fan-out
- IsolationForest baseline + paired bootstrap CI comparison
- Supervisor + conflict resolver (hybrid rule+LLM), structured failure logging
- Streamlit UI (four panels, scenario dropdown)
- Unified `make eval` harness → `RESULTS.md`
- Space-Track MCP facade
- ADRs 0001–0007, v1.0.0-rc1 tagged

**Next:** REPORT.md finalization, 3-min demo recording, résumé bullet, flip repos public, v1.0.0

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
- Anthropic credit expired June 16; provider flipped to Groq. See ADR-0002.
- Snapshot tests (`syrupy`) lock expected behavior. If a test fails after a
  prompt change, that's the signal — review the diff, decide intentional or
  regression, update snapshot only if intentional.

## Harness discipline

Every week has a harness deliverable. Skipping it once is a warning. Skipping
twice is a sign to pause and recalibrate. See `AMOA_PLAN.md` Section 3 for
the weekly harness table.

## Skill routing

When the user's request matches an available skill, invoke it via the Skill tool. When in doubt, invoke the skill.

Key routing rules:
- Product ideas/brainstorming → invoke /office-hours
- Strategy/scope → invoke /plan-ceo-review
- Architecture → invoke /plan-eng-review
- Design system/plan review → invoke /design-consultation or /plan-design-review
- Full review pipeline → invoke /autoplan
- Bugs/errors → invoke /investigate
- QA/testing site behavior → invoke /qa or /qa-only
- Code review/diff check → invoke /review
- Visual polish → invoke /design-review
- Ship/deploy/PR → invoke /ship or /land-and-deploy
- Save progress → invoke /context-save
- Resume context → invoke /context-restore
- Author a backlog-ready spec/issue → invoke /spec

