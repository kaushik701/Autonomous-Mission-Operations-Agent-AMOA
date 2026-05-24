# AMOA — Master Plan

**Version:** 3 (final)
**Date:** Tuesday May 19, 2026
**Supersedes:** scoping doc, implementation plan, reworked schedule (delete those after Saturday)

This document is the single source of truth for AMOA's scope, schedule, approach, and stack. Re-read it weekly during the Friday review.

---

## 1. The Project, in One Paragraph

AMOA (Autonomous Mission Operations Agent) is a multi-agent LLM system that coordinates three concerns of satellite mission operations — collision avoidance, hardware health monitoring, and payload imagery analysis — under a LangGraph supervisor with a conflict resolver. It runs locally as a digital-twin simulation against real public data (NASA Space-Track CDMs, ESA Anomaly Dataset, Sentinel-2 imagery via Copernicus). The project produces three artifacts: the AMOA system itself, an open-source MCP server for NASA Space-Track, and an evaluation harness demonstrating rigorous LLM-system testing. It's a portfolio project for AI/ML engineering job applications, not flight software.

## 2. Locked Decisions

These don't change. Re-read this section when tempted to expand scope.

| Decision | Value | Source |
|---|---|---|
| Primary claim | Systems + Infrastructure | Scoping Decision 1 = C |
| Résumé treatment | Replaces AIFlow | Scoping Decision 2 = A |
| Weekly time budget | 10.5 hours | Revised Decision 3 (downgraded from 16) |
| Total weeks | 8 | Derived from budget |
| Start date | Saturday May 23, 2026 | W0 scaffolding day |
| End date | Saturday July 12, 2026 | W7 ship day |
| Approach to LLM systems work | Medium harness | Confirmed May 19 |
| Open-source artifact | `spacetrack-mcp` repo | Part of systems+infra claim |
| Demo target | Local + recorded walkthrough | No cloud deploy this iteration |

## 3. What Medium Harness Means in Practice

Harness engineering — building the scaffolding that makes LLM systems reliable, observable, and testable — runs as a parallel thread through every week. Not a separate phase. Each week adds a small harness deliverable that compounds.

| Week | Primary work | Harness deliverable |
|---|---|---|
| W0 | Scaffolding | Test infra (pytest config), `.env` discipline |
| W1 | Safety Pilot | `llm.py` with retry-with-correction + failure-mode log |
| W2 | Health Guard + baseline | Statistical comparison (paired bootstrap CI) |
| W3 | Payload Scientist | Snapshot testing pattern |
| W4 | Supervisor + Resolver | Structured failure logging into supervisor state |
| W5 | UI + Eval consolidation | `make eval` unified harness, provider comparison |
| W6 | MCP server | MCP-specific eval suite |
| W7 | Polish + ship | "Evaluation & Reliability" section in REPORT.md |

**What you get by the end:**

- Pydantic schemas at every function boundary that crosses a module
- A failure-mode taxonomy grown weekly (schema violation, refusal, timeout, rate limit, hallucination, malformed tool call)
- Snapshot tests locking expected behavior on canonical inputs
- Statistical rigor on the Claude-vs-Llama comparison
- Provider abstraction via `llm.py` — switch providers with one env var
- LangSmith tracing across all agent calls
- A unified eval harness invokable via `make eval`
- Each PR runs the eval; regressions surface before merge (manually inspected, not auto-gated)

**What we are NOT building (saved you from heavy):**

- Automatic regression gating in CI (would require GitHub Actions setup + thresholds)
- Cost/latency budget enforcement that fails builds
- A formal "test fixture generation" pipeline using LLMs to create fixtures

These are real harness work and worth knowing about for interviews, but cost 1+ week extra and don't fit the 10.5 hr/week budget. Mention them in REPORT.md as "future work."

**The non-negotiable for medium to work:**

Every week's harness deliverable happens. Not "if I have time." Skipping the W2 statistical comparison or the W3 snapshot tests collapses medium back to light. The 1 extra hour per week is the thing that compounds.

## 4. Tech Stack (Final, Locked)

### Libraries

| Layer | Library | Purpose |
|---|---|---|
| Orchestration | `langgraph` | Supervisor + Send fan-out for parallel agents |
| Schemas | `pydantic` v2 | Output enforcement on every agent |
| HTTP | `httpx` | Async-first, used by spacetrack |
| Space-Track | `spacetrack` | Auth, rate limiting, query types |
| Baselines | `scikit-learn` | IsolationForest |
| Statistics | `scipy.stats` | Bootstrap CIs for paired comparisons (medium harness) |
| LLM clients | `anthropic`, `google-generativeai`, `groq` | Official SDKs, never wrapped |
| MCP (W6) | `mcp` | Official Anthropic Python SDK |
| UI | `streamlit` | Minimal demo surface in W5 |
| Observability | `langsmith` | Free tier, LangChain-native |
| Persistence | `sqlmodel` (SQLite) | Run history, interview talking point |
| Caching | `diskcache` | Preserves API quotas during dev |
| Snapshot testing | `syrupy` | Locks expected outputs for regression detection |
| Package mgmt | `uv` | Fast, simple, modern |
| Lint / test | `ruff`, `pytest`, `pytest-asyncio` | Day-one habits |

### LLM Provider Strategy

| Agent | Provider until June 16 | Provider after June 16 |
|---|---|---|
| Safety Pilot | Claude Sonnet 4.5 | Groq Llama 3.3 70B |
| Health Guard | Gemini 2.5 Flash-Lite | Gemini 2.5 Flash-Lite |
| Payload Scientist | Gemini 2.5 Flash Vision | Gemini 2.5 Flash Vision |
| Conflict Resolver | Claude Sonnet 4.5 | Groq Llama 3.3 70B |
| Hello-world (W0) | Claude Sonnet 4.5 | n/a |

Anthropic credit: $49.35 balance, $40 hard cap. Strategy detailed in ADR-0002.

### Tooling

- **Claude Code (terminal):** primary single-file work, debugging, agent iteration
- **Antigravity:** multi-file refactors (W4 supervisor wire-up, W6 MCP refactor)
- **Claude Desktop:** planning, weekly reviews, prompt brainstorming — context lives in the AMOA Project
- **gstack skills inside Claude Code:** `/investigate`, `/review`, `/qa`, `/ship` — workflow discipline
- **No claude-flow.** AMOA *is* the multi-agent orchestration project; running it under another orchestration framework dilutes the systems claim

## 5. Data Sources (Verified)

| Source | Status | Access | Limits | Used by |
|---|---|---|---|---|
| Space-Track REST API | Live | Free, registration | 30/min, 300/hr | Safety Pilot |
| `spacetrack` Python lib | Mature, MIT | `pip install spacetrack` | Handles throttling | Safety Pilot |
| ESA Anomaly Dataset, Mission 1 only | Live | Zenodo, CC-BY | ~500MB-1GB subset | Health Guard |
| Copernicus Data Space (Sentinel-2) | Live | Free, registration | STAC + OData | Payload Scientist |
| Existing NASA-MCP servers | Reference | GitHub | n/a | W6 reference reading |
| Space-Track MCP server | **Does not exist** | — | — | **You build this in W6** |

## 6. The 8-Week Schedule

Weeknight blocks: Mon-Fri 8:00 – 9:30 PM (90 min each, 7.5 hr/week).
Saturday block: 10:00 AM – 1:00 PM (3 hr).
Sunday: rest.
Friday 9:30 – 10:00 PM: end-of-week review + Claude session for next week's task file.

### W0 — Scaffolding (Saturday May 23, 3 hours)

Single Saturday block, see `AMOA_W0.md` for the step-by-step.

### Week of May 19 (pre-W0, this week)

- **Tonight (Tue May 19):** logistics — Calendar updated, Anthropic cap set, reply with blockers list
- **Wed May 20:** read this plan + `AMOA_CLAUDE_CODE.md` + `AMOA_W0.md` end to end. Take notes.
- **Thu May 21:** verify Space-Track and Copernicus accounts (login, click around). Install Antigravity if not done.
- **Fri May 22:** start ESA Mission 1 download from Zenodo. Friday review note.
- **Sat May 23 10 AM:** W0 scaffolding day.

### W1 — Safety Pilot Foundation (May 26 – June 1)

| Block | Work |
|---|---|
| Mon | Space-Track verification notebook — auth, one TLE pull, one CDM pull |
| Tue | Build `src/amoa/llm.py` (provider abstraction) + 3 negative tests for schema failures |
| Wed | Safety Pilot Pydantic schemas + system prompt draft |
| Thu | Safety Pilot end-to-end with mocked CDM fixture |
| Fri | Wire Safety Pilot as a LangGraph node + Friday review |
| Sat | 3 scenario fixture tests (no risk / moderate / imminent) + ADR-0002 (provider strategy) + v0.2.0 tag |

**Harness deliverable:** `llm.py` includes retry-with-correction on schema violation, failure categorization (logged to `eval/failures.jsonl`), and 3 negative tests verifying that malformed LLM outputs trigger correct error paths.

**DoD:** Safety Pilot returns a validated `SafetyAssessment` from a real Space-Track CDM. Three tests pass. ADR-0002 written. v0.2.0.

### W2 — Health Guard + Baseline (June 2 – June 8)

| Block | Work |
|---|---|
| Mon | Real Space-Track CDMs (replace mocks) + disk cache wrapper |
| Tue | ESA loader (`esa_loader.py`) — windowed, < 1 GB RAM |
| Wed | Isolation forest baseline — train + eval, save metrics |
| Thu | Health Guard agent (Gemini Flash-Lite) — structured output |
| Fri | Wire Health Guard into graph + Friday review |
| Sat | Statistical comparison — paired bootstrap CI on F1 difference (Health Guard vs isolation forest) + ADR-0003 (data layer choices) + v0.3.0 |

**Harness deliverable:** Statistical comparison using `scipy.stats.bootstrap` produces a confidence interval and p-value on the F1 difference between the two methods. Result table in REPORT.md includes the CI.

**DoD:** `make eval` runs both Health Guard and isolation forest on shared windows. Results table includes statistical confidence. v0.3.0.

### W3 — Payload Scientist (June 9 – June 15)

| Block | Work |
|---|---|
| Mon | Curate 8-10 Sentinel-2 fixture scenes (Copernicus Browser, manual) |
| Tue | `sentinel_loader.py` — GeoTIFF read, resize, base64 |
| Wed | Payload Scientist agent (Gemini Flash Vision) |
| Thu | Wire into graph + first eval pass |
| Fri | Snapshot testing pattern with `syrupy` + Friday review |
| Sat | Apply snapshot pattern to Safety Pilot + Health Guard also + v0.4.0 |

**Harness deliverable:** `syrupy`-based snapshot tests for all three agents. Canonical inputs → locked expected output shapes. Catches behavior drift on prompt changes.

**DoD:** All three agents work end-to-end. Snapshot tests pass for all three. v0.4.0.

### W4 — Supervisor + Conflict Resolver (June 16 – June 22)

**Anthropic credit expires Tuesday June 16. Provider swap happens Wednesday.**

| Block | Work |
|---|---|
| Mon | Final `MissionState` schema with all three agent assessments |
| Tue | **Last Claude-Sonnet day.** Implement supervisor + Send fan-out |
| Wed | **Flip `AMOA_LLM_PROVIDER=groq`.** Re-run W1-W3 tests, fix prompt issues |
| Thu | Conflict resolver (hybrid: rules + LLM) with structured failure logging |
| Fri | Three canned scenarios (clear / conflict / degraded) + Friday review |
| Sat | Stress test the full graph + LangSmith trace screenshots + v0.5.0 |

**Harness deliverable:** Supervisor logs structured failures (agent timeout, schema violation, refusal) into `MissionState.failure_log`. Conflict resolver receives this signal and reacts accordingly. Visible in LangSmith traces.

**DoD:** `python -m amoa.graph --scenario conflict` runs full graph, resolver picks safety over payload, exits clean. Failure logging visible in state. v0.5.0.

### W5 — UI + Eval Harness Consolidation (June 23 – June 29)

| Block | Work |
|---|---|
| Mon | Full eval suite run on Groq — compare to last Claude run. Save metrics. |
| Tue | Streamlit UI — four panels, scenario dropdown |
| Wed | UI continued — live state rendering, scenario tick |
| Thu | Eval harness consolidation — single `make eval` runs all tests, statistical comparisons, snapshot checks, produces a markdown results table |
| Fri | LangSmith dashboards + screenshots + Friday review |
| Sat | UI polish + 30-sec demo screen capture + v0.6.0 |

**Harness deliverable:** `make eval` is the unified harness. Runs ~30-50 fixture tests across three agents, two providers, with statistical comparisons. Output is `eval/results/RESULTS.md` — committed alongside code so progress is visible in git history.

**DoD:** `make demo` boots the UI. `make eval` produces the unified results table. v0.6.0.

### W6 — MCP Server Refactor (June 30 – July 6)

| Block | Work |
|---|---|
| Mon | Read existing NASA-MCP servers as reference. Sketch `spacetrack-mcp` design. |
| Tue | Create `spacetrack-mcp` repo. Wrap `spacetrack` lib with `mcp` SDK. Three tools: `tle_lookup`, `conjunction_query`, `satcat_search`. |
| Wed | MCP-specific eval suite (input validation, output schema compliance, latency). |
| Thu | MCP README — install, Claude Desktop config example, screenshot |
| Fri | Refactor AMOA to use MCP server instead of importing `spacetrack` directly + Friday review |
| Sat | Example consumer notebook + LICENSE (MIT) + publish public + v1.0.0-rc1 |

**Harness deliverable:** MCP server has its own pytest suite verifying tool inputs/outputs match advertised schemas and that latency stays under documented bounds.

**DoD:** Two repos. MCP server installable via `uvx`. Both READMEs polished. v1.0.0-rc1.

### W7 — Final Polish + Recording (July 7 – July 12)

| Block | Work |
|---|---|
| Mon | REPORT.md — Architecture section finalized with Mermaid diagram |
| Tue | REPORT.md — Methodology + Results sections finalized |
| Wed | REPORT.md — "Evaluation & Reliability" section (the harness narrative) |
| Thu | Record 3-min narrated walkthrough video, upload to YouTube unlisted |
| Fri | Draft 3 versions of résumé bullet, pick best, update résumé, remove AIFlow |
| Sat | AMOA repo flipped public + v1.0.0 tagged + done |

**DoD:** Two public repos, one demo video, one updated résumé. Project ships.

## 7. Risks (Updated for Medium + 8 Weeks)

| Risk | Mitigation | Trigger |
|---|---|---|
| "Felt lazy" pattern repeats | Friday review surfaces it honestly; pause if 2 weekday blocks skipped in a row | Tell me, don't grind silently |
| Job interview eats a week | Plan is pause-able at any tagged version | Skip W6 (MCP) before skipping the harness work |
| Anthropic credit expires mid-W4 | `llm.py` from W1 makes swap a one-env-var change | Wed June 17 is the planned swap day |
| Free-tier rate limits during eval | Aggressive `diskcache`; dev fixtures bypass live API | If hitting 429s, pause and audit |
| 6 GB RAM hits ceiling | ESA windowed loading; close VS Code when running Streamlit | Watch page file |
| W4 supervisor doesn't converge | Sequential pipeline fallback (Safety → Health → Payload → Resolver) | Wed of W4 not working = ship fallback |
| Demo crashes during recording | Pre-cache all API responses for the recorded run | Always have a recorded fallback |
| Scope creep | Re-read Section 2 (locked decisions) and Section 3 (medium boundaries) | If urge persists 3 days, write down why, then say no |

## 8. Working Rhythm

- **Daily 90 min** at the same time, Mon-Fri 8:00–9:30 PM
- **Saturday 3 hr** 10 AM – 1 PM, single block
- **Sunday off** — non-negotiable rest
- **Friday 9:30–10:00 PM:** review + ping me for next week's task file

**Pause discipline:**

- 1 skipped weeknight: do it Saturday morning, no narrative
- 2 skipped weeknights in a row: pause, tell me, descope or extend
- Whole week missed: rebase the timeline; ship date slips, scope doesn't expand to compensate

## 9. What "Done" Means at W7 Sat

By end of Saturday July 12, you have:

- ✅ `amoa` public GitHub repo, install-to-demo in 15 min
- ✅ `spacetrack-mcp` public GitHub repo, installable via `uvx`
- ✅ 3-min narrated demo video, linked from both READMEs
- ✅ REPORT.md, 2000-2500 words, architecture + methodology + results + harness narrative
- ✅ Updated résumé bullet replacing AIFlow
- ✅ ADRs 0001-0007 written

**Résumé bullet target (refine in W7):**

> Built AMOA, a multi-agent satellite mission operations system (LangGraph + Claude/Gemini/Groq) with three specialized agents under an async supervisor; designed harness with Pydantic-enforced boundaries, snapshot tests, and statistical baselines (paired bootstrap CIs); open-sourced companion Space-Track MCP server, first of its kind. Python, async, scikit-learn, Streamlit.

## 10. How We Work Together

- I plan, push back, review code, ask you to explain things back. I don't write the project for you.
- New chats happen inside the AMOA Project in Claude Desktop so context persists.
- Friday review: ping with "ready for W[N+1]" and I write the next week's task file in that session.
- Mid-week problems: open a chat, paste the error, we debug. 20-min stuck rule — don't grind silently.
- Mid-week feature ideas: write them in `IDEAS_PARKING_LOT.md` (you create this in W0). Revisit during W7 polish.
- If I keep getting dates wrong (it happened once already), correct me. The plan is anchored to your reality, not mine.

---

That's the plan. Two more documents follow: `AMOA_CLAUDE_CODE.md` (the structure for your repo) and `AMOA_W0.md` (Saturday May 23 step-by-step).
