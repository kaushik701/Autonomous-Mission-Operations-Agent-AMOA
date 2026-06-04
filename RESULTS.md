# AMOA Eval Results
Generated: 2026-06-04 05:28 UTC

| Scenario | Safety | Health | Action | Confidence | Degraded | Failures |
|---|---|---|---|---|---|---|
| clear | LOW | NOMINAL | NOMINAL_OPS | 95% | False | 0 |
| conflict | HIGH | WARNING | MANEUVER | 95% | False | 0 |
| degraded | MEDIUM | — | NOMINAL_OPS | 60% | True | 1 |

## Notes

- Scenario fixtures in `tests/fixtures/scenarios/`
- Agent nodes mocked — no live LLM calls
- Resolver rule: Safety HIGH → MANEUVER; else NOMINAL_OPS
- `degraded=True` when any agent failure logged
