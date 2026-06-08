# ADR-0007: Separate Space-Track Access Behind an MCP Facade

**Date:** 2026-06-07
**Status:** Accepted
**Week:** W4 (wiring complete in W6)

## Context

`spacetrack_client.py` imports the `spacetrack` Python library directly and
calls `client.gp(...)` and `client.cdm(...)` inline. This couples every agent
that needs orbital data to a specific Python package, a specific auth flow, and
a specific rate-limit contract.

The project `IDEAS_PARKING_LOT.md` sketched a `spacetrack-mcp` server that
exposes `tle_lookup` and `cdm_fetch` as MCP tools. That sketch raises a
question that this ADR answers: *when and why to commit to the MCP boundary
rather than keeping the direct lib call*.

## Decision

Split `spacetrack_client.py` into two modules:

1. **`spacetrack_client_direct.py`** — owns the `spacetrack` lib import,
   diskcache wiring, and the mock-CDM fallback. Nothing outside this module
   imports the `spacetrack` package.

2. **`spacetrack_client.py`** — MCP-shaped facade. Exports
   `fetch_tle_via_mcp` and `fetch_cdms_via_mcp`. Today these delegate to
   `_direct`; in W6 they call an `mcp.ClientSession` over stdio/SSE.

Agents import only from `spacetrack_client.py`. They never see the transport.

## Why

**Provider-agnostic agents.** The Safety Pilot's job is collision avoidance
reasoning, not HTTP auth management. Pushing the transport behind a facade
keeps the agent file focused on prompt logic.

**Single swap point for W6.** When the live MCP server is ready, the change
is two function bodies in one file — not a grep-and-replace across the agent
layer. The interface (function name, argument types, return types) is frozen
now.

**Interview story.** "I separated the MCP contract from the implementation so
the architectural decision is visible even before the network hop is live."
This is more defensible than "I wrote a wrapper because it might be useful
someday."

**Testability.** Tests can monkeypatch `spacetrack_client._fetch_tle` without
touching the `spacetrack` lib at all. The facade is the seam.

## Trade-offs

**Extra indirection for no immediate runtime benefit.** Today both modules are
local Python; there is no process boundary, no serialization, no latency
difference. The split is purely organizational until W6.

**`spacetrack_client_direct.py` stays coupled to the lib.** Moving the import
one file over does not remove the dependency from the project. `spacetrack`
still appears in `pyproject.toml` until W6 replaces it with `mcp`.

**Accepted:** the split pays off at W6 with a surgical one-file edit and a
clean git diff that reviewers can audit in isolation.

## Alternatives Rejected

**Keep the direct lib call, add a TODO comment.** This was the original state.
Rejected because a comment has no enforcement — future agent code can import
from `_direct` accidentally, and the "MCP separation" story evaporates.

**Full MCP wiring now (W4).** Rejected. The `mcp` client SDK adds async
complexity (`ClientSession`, subprocess management for the server process)
that is W6 scope. Doing it now burns two weeks of harness budget for a feature
that has no user-facing impact until W6.

**Abstract base class / protocol.** A `SpaceTrackProvider` ABC would let us
swap implementations by injecting a different object. Rejected — three uses
before refactoring; we have exactly one call site per function. An ABC would
be a premature abstraction on top of a facade that is already doing the job.

## Consequences

- Agents import `from amoa.data.spacetrack_client import fetch_tle_via_mcp`.
  No agent file imports `spacetrack_client_direct` or the `spacetrack` lib.
- W6 work: implement `mcp.ClientSession` calls in the two function bodies in
  `spacetrack_client.py`; `spacetrack_client_direct.py` can then be deleted
  or archived.
- If the live MCP server is never built (scope cut), the facade still works
  indefinitely — the direct lib call is a valid permanent fallback.
