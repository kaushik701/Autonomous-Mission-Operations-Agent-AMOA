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
