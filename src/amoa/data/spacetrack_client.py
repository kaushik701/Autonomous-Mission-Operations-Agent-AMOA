"""
Space-Track MCP facade.

Agents call fetch_tle_via_mcp / fetch_cdms_via_mcp. These delegate to the
direct spacetrack-lib implementation in spacetrack_client_direct.py. The
interface is identical to what an mcp.ClientSession transport would expose —
swapping the transport leaves agent code unchanged.
"""
from amoa.data.cdm import CDM
from amoa.data.spacetrack_client_direct import fetch_tle as _fetch_tle
from amoa.data.spacetrack_client_direct import fetch_cdms as _fetch_cdms


def fetch_tle_via_mcp(norad_id: int) -> str:
    """Return latest TLE string for norad_id."""
    # In production: mcp.ClientSession call to spacetrack-mcp server
    # For now: direct lib call — same interface, no behavioral change
    return _fetch_tle(norad_id)


def fetch_cdms_via_mcp(limit: int = 10) -> tuple[list[CDM], bool]:
    """Return (cdm_records, is_mock) for the most recent conjunctions."""
    # In production: mcp.ClientSession call to spacetrack-mcp server
    # For now: direct lib call — same interface, no behavioral change
    return _fetch_cdms(limit)
