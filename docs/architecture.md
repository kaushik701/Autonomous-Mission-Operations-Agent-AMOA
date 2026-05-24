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
