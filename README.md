# AMOA — Autonomous Mission Operations Agent

Multi-agent satellite mission coordination via LangGraph + Claude/Gemini/Groq.

**Status:** Week 0 — scaffolding. Not yet functional.

## Setup

```bash
uv sync
cp .env.example .env
# Fill in API keys
uv run python -m amoa.graph
```

## Roadmap

- [x] W0: Scaffolding + hello-world graph
- [ ] W1: Safety Pilot + Space-Track integration + `llm.py` provider abstraction
- [ ] W2: Health Guard + ESA Anomaly Dataset baseline + statistical comparison
- [ ] W3: Payload Scientist + Sentinel-2 + snapshot testing
- [ ] W4: Supervisor + LangGraph topology + provider swap to Groq
- [ ] W5: Streamlit UI + unified eval harness
- [ ] W6: MCP server refactor + public release
- [ ] W7: Polish, recording, ship

Project plan in `AMOA_PLAN.md`.
