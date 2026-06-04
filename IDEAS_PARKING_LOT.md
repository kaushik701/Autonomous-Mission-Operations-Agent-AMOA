spacetrack-mcp tools:
- tle_lookup(norad_id: int) → str
- conjunction_query(limit: int, min_pc: float) → list[dict]
- satcat_search(name: str) → list[dict]

Auth: SPACETRACK_USERNAME + SPACETRACK_PASSWORD from env
Rate limiting: delegate to spacetrack lib
Caching: diskcache, same as AMOA

---

## spacetrack-mcp Design Sketch (W6 MCP milestone)

*Research basis: ProgramComputer/NASA-MCP-server, MaxwellCalkin/N2YO-MCP,
nasa/earthdata-mcp, NASA-PDS/pds-mcp-server, and the official
modelcontextprotocol.io FastMCP build guide. All four real-world servers
use the same structural pattern: FastMCP + Python type hints drive the
JSON schema; env-var credentials loaded at server startup; no credential
passing through individual tool calls.*

### Background

AMOA W6 adds MCP tool exposure so that external LLM agents (or Claude
Desktop) can call into AMOA's data layer directly. Space-Track is the
NASA/DoD source for TLEs, conjunction data messages (CDMs), and the
satellite catalog (SATCAT). The `spacetrack` Python library already lives
in the project and handles cookie-based session auth and rate-limit
throttling. The MCP server is a thin wrapper — it must NOT re-implement
auth or throttling; it delegates entirely to the existing `spacetrack_client.py`.

---

### Tool List

Each tool maps 1-to-1 to a function already in `spacetrack_client.py` or
a simple extension of it. Input schemas are derived from Python type hints;
FastMCP generates the JSON schema automatically.

#### `get_tle`

```
Input:
  norad_id: int           -- NORAD catalog number (e.g. 25544 for ISS)

Returns: str
  Two-line element set (line 0 = name, line 1 = TLE line 1, line 2 = TLE line 2)
  Newline-separated. Cached 1 hour (matches spacetrack_client.fetch_tle).

Example return:
  "ISS (ZARYA)\n1 25544U 98067A   ...\n2 25544  ..."
```

Evidence basis: N2YO-MCP exposes `get_satellite_tle(noradId: string)` with
the same single-parameter pattern; NASA-MCP-server tools each take 1-3
typed params; FastMCP infers the schema from the type hint.

#### `get_cdm`

```
Input:
  limit: int = 10         -- max records to return (Space-Track hard cap: 1000)
  min_pc: float = 0.0     -- filter: only return CDMs where PC >= min_pc

Returns: list[dict]
  Each dict is a CDM record with keys matching the CDM Pydantic model:
  cdm_id, created, tca, miss_distance, probability_of_collision,
  relative_speed, relative_position_r/t/n,
  sat1_norad_id, sat1_name, sat1_object_type,
  sat2_norad_id, sat2_name, sat2_object_type, emergency_reportable.
  Returns mock data (flagged with is_mock=true) when account lacks CDM tier.

Example return (one record abbreviated):
  [{"cdm_id": 100001, "tca": "2026-06-04T12:00:00Z",
    "miss_distance": 312.5, "probability_of_collision": 4.7e-05,
    "sat1_name": "SENTINEL-2A", "sat2_name": "COSMOS 2251 DEB",
    "emergency_reportable": false, "is_mock": false}]
```

The `min_pc` filter is applied in Python after fetching, not as a
Space-Track query param, because the CDM endpoint does not support
server-side PC filtering.

#### `list_conjunctions`

```
Input:
  norad_id: int           -- filter: only conjunctions involving this object
  days_ahead: int = 7     -- TCA must be within this many days from now
  limit: int = 20         -- max records

Returns: list[dict]
  Same schema as get_cdm but pre-filtered to the given object and time window.
  Sorted ascending by TCA.

Notes:
  Calls fetch_cdms internally with a larger limit, then filters in Python.
  This avoids multiple Space-Track round-trips and stays within rate limits.
```

#### `satcat_search`

```
Input:
  name: str               -- partial name match (case-insensitive LIKE query)
  limit: int = 10

Returns: list[dict]
  Keys: norad_cat_id, satname, object_type, launch_date, country, period_min,
        inclination, apogee_km, perigee_km, decay_date (null if still up)

Example return:
  [{"norad_cat_id": 43013, "satname": "SENTINEL-2B",
    "object_type": "PAYLOAD", "country": "ESA",
    "inclination": 98.57, "apogee_km": 786, "perigee_km": 785}]
```

Evidence basis: N2YO-MCP has `search_satellites_by_name(query)` and
`get_satellites_by_category(category, country)` — same decomposition.
NASA-MCP-server has `nasa/sbdb` (small-body database) with similar
name-search semantics.

#### `get_decay_forecast`

```
Input:
  norad_id: int
  days: int = 30          -- look-ahead window

Returns: dict | None
  Keys: norad_cat_id, satname, decay_epoch (ISO UTC), decay_region (str),
        confidence (str: HIGH | MEDIUM | LOW | INDETERMINATE).
  None if no decay predicted within the window.

Notes:
  Thin wrapper over Space-Track /class/decay/. Cached 6 hours.
  Low priority for W6 MVP; include in schema now, implement after get_tle
  and get_cdm are green.
```

---

### Auth Approach

Space-Track uses cookie-based session auth — the `spacetrack` Python library
logs in with username + password, stores a session cookie internally, and
auto-refreshes when the ~2-hour cookie TTL lapses. AMOA's
`spacetrack_client.get_client()` already encapsulates this.

The MCP server follows the pattern used by every NASA MCP server surveyed:
credentials come from environment variables, loaded once at server startup,
never passed as tool arguments.

```
Environment variables (same names as existing AMOA .env):
  SPACETRACK_USERNAME   -- Space-Track account email
  SPACETRACK_PASSWORD   -- Space-Track account password

The server reads these via amoa.config.settings (Pydantic BaseSettings).
No new env vars needed. No API key header; no OAuth flow.
```

Implementation note: the `spacetrack` lib creates a new HTTP session per
`SpaceTrackClient()` instance. For the MCP server, create one module-level
client at startup (FastMCP lifespan or top-of-module) and reuse it across
tool calls to avoid redundant logins burning rate-limit quota.

---

### Rate Limits

Space-Track enforces two hard limits:

| Window | Limit | Handling |
|--------|-------|----------|
| Per minute | 30 requests | `spacetrack` lib throttles automatically |
| Per hour | 300 requests | `spacetrack` lib throttles automatically |

The MCP server adds a second layer of protection via `diskcache`:

- `get_tle`: cached 1 hour (matches existing `spacetrack_client.fetch_tle`)
- `get_cdm` / `list_conjunctions`: cached 30 minutes (CDMs refresh ~every 8 h)
- `satcat_search`: cached 24 hours (SATCAT is rarely updated mid-day)
- `get_decay_forecast`: cached 6 hours

Never bypass the `spacetrack` lib's internal throttle. Do not call
`SpaceTrackClient` methods in a tight loop from the MCP server side.

---

### Example README Snippet

How an LLM agent (e.g. Safety Pilot running via AMOA graph) would call
the tools through Claude Desktop or an MCP client:

```json
// claude_desktop_config.json
{
  "mcpServers": {
    "spacetrack": {
      "command": "uv",
      "args": ["--directory", "/path/to/amoa", "run", "src/amoa/mcp/server.py"],
      "env": {
        "SPACETRACK_USERNAME": "you@example.com",
        "SPACETRACK_PASSWORD": "hunter2"
      }
    }
  }
}
```

Agent interaction (natural language → tool call → structured result):

```
User:  "Is SENTINEL-2A in any close approaches this week?"

Agent calls:  list_conjunctions(norad_id=43013, days_ahead=7, limit=5)

Server returns:
[
  {
    "cdm_id": 200341,
    "tca": "2026-06-05T08:14:22Z",
    "miss_distance": 412.0,
    "probability_of_collision": 2.1e-06,
    "sat1_name": "SENTINEL-2A",
    "sat2_name": "COSMOS 1408 DEB",
    "emergency_reportable": false,
    "is_mock": false
  }
]

Agent response: "SENTINEL-2A has one close approach this week, on June 5
at 08:14 UTC, with COSMOS 1408 DEB at 412 m miss distance.
Probability of collision is 2.1 × 10⁻⁶ — below the emergency threshold."
```

Python snippet an engineer would use to call the server directly:

```python
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def check_sentinel():
    server_params = StdioServerParameters(
        command="uv",
        args=["run", "src/amoa/mcp/server.py"],
    )
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(
                "list_conjunctions",
                {"norad_id": 43013, "days_ahead": 7, "limit": 5},
            )
            print(result.content)
```

---

### Server Implementation Outline

File location: `src/amoa/mcp/server.py`

```python
from mcp.server.fastmcp import FastMCP
from amoa.data.spacetrack_client import fetch_tle, fetch_cdms
from amoa.data.cdm import CDM

mcp = FastMCP("spacetrack-mcp")

@mcp.tool()
async def get_tle(norad_id: int) -> str:
    """Return the latest two-line element set for a NORAD catalog ID."""
    return fetch_tle(norad_id)          # sync is fine; diskcache hit is fast

@mcp.tool()
async def get_cdm(limit: int = 10, min_pc: float = 0.0) -> list[dict]:
    """Return recent conjunction data messages, optionally filtered by PC."""
    records, is_mock = fetch_cdms(limit=limit)
    out = [r.model_dump() for r in records if r.probability_of_collision >= min_pc]
    for row in out:
        row["is_mock"] = is_mock
    return out

# ... list_conjunctions, satcat_search, get_decay_forecast follow same pattern

if __name__ == "__main__":
    mcp.run(transport="stdio")
```

Tools are async; the underlying `fetch_*` functions are sync with diskcache.
Run sync calls in `asyncio.get_event_loop().run_in_executor(None, fn)` if
blocking becomes an issue under load (unlikely for a single-user dev server).

---

### Fit into AMOA W6 MCP Milestone

AMOA_PLAN.md lists W6 as "MCP tool exposure". This server delivers:

1. External agents (Claude Desktop, custom clients) can query Space-Track
   data through standardized MCP tool calls without importing AMOA internals.
2. Safety Pilot can be refactored to call `get_cdm` / `list_conjunctions`
   via MCP rather than importing `spacetrack_client` directly — decoupling
   the agent from the data layer.
3. The server reuses `spacetrack_client.py`, `cdm.py`, and `config.py` with
   zero duplication. The only new file is `src/amoa/mcp/server.py` (~80 lines).
4. `diskcache` integration means the MCP server and the main AMOA graph share
   the same cache — a TLE fetched by Safety Pilot is available to an external
   MCP caller without a second Space-Track hit.

MVP scope for W6: `get_tle` + `get_cdm` + `list_conjunctions`. `satcat_search`
and `get_decay_forecast` are stretch goals if time permits.

Dependencies to add to `pyproject.toml`:
  `mcp[cli]>=1.2.0`   (FastMCP is bundled since MCP SDK 1.2)

---

### Open Questions / Risks

- Space-Track CDM access: account is still pending CDM tier approval.
  `get_cdm` and `list_conjunctions` will return mock data until approved.
  The `is_mock` flag in the return shape surfaces this to callers.
- STDIO vs HTTP transport: STDIO is simpler for local dev and Claude Desktop.
  If AMOA adds a Streamlit-hosted MCP endpoint later, switch to
  `transport="streamable-http"`. No code change needed other than the
  `mcp.run()` call.
- Thread safety of `SpaceTrackClient`: the `spacetrack` lib is not
  documented as thread-safe. Use a single module-level instance; if
  concurrent tool calls hit a race, add an `asyncio.Lock` around the
  client calls.