"""
Space-Track client — W6 MCP facade.

Agents call fetch_tle_via_mcp / fetch_cdms_via_mcp.  Today those delegate
to the direct spacetrack-lib implementation in spacetrack_client_direct.py.
In W6, replace the body of each function with an mcp.ClientSession tool call:

    async with mcp.ClientSession(...) as session:
        result = await session.call_tool("tle_lookup", {"norad_id": norad_id})
        return result.content[0].text

The interface stays identical; only the transport changes.
"""
from amoa.data.cdm import CDM
from amoa.data.spacetrack_client_direct import fetch_tle as _fetch_tle
from amoa.data.spacetrack_client_direct import fetch_cdms as _fetch_cdms


def fetch_tle_via_mcp(norad_id: int) -> str:
    """Return latest TLE string for norad_id.

    W6 upgrade: replace body with mcp ClientSession.call_tool("tle_lookup", ...).
    """
    # In production: mcp.ClientSession call to spacetrack-mcp server
    # For now: direct lib call — same interface, no behavioral change
    return _fetch_tle(norad_id)


def fetch_cdms_via_mcp(limit: int = 10) -> tuple[list[CDM], bool]:
    """Return (cdm_records, is_mock) for the most recent conjunctions.

    W6 upgrade: replace body with mcp ClientSession.call_tool("cdm_fetch", ...).
    """
    # In production: mcp.ClientSession call to spacetrack-mcp server
    # For now: direct lib call — same interface, no behavioral change
    return _fetch_cdms(limit)
