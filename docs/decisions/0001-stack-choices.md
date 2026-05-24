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
