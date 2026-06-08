"""
Direct spacetrack-lib implementation — used by spacetrack_client.py as the
fallback while the live MCP server is not yet wired (W6 upgrade path).

Nothing outside spacetrack_client.py should import from here.
"""
import json

import diskcache
import httpx
from spacetrack import SpaceTrackClient

from amoa.config import settings
from amoa.data.cdm import CDM, mock_cdm_factory

cache = diskcache.Cache(settings.diskcache_dir)


def _get_client() -> SpaceTrackClient:
    return SpaceTrackClient(
        identity=settings.spacetrack_username,
        password=settings.spacetrack_password,
    )


def fetch_tle(norad_id: int) -> str:
    """Fetch latest TLE for a NORAD ID. Cached 1 hour."""
    key = f"tle:{norad_id}"
    if key in cache:
        return cache[key]
    client = _get_client()
    result = client.gp(norad_cat_id=norad_id, orderby="epoch desc", limit=1, format="tle")
    cache.set(key, result, expire=3600)
    return result


def fetch_cdms(limit: int = 10) -> tuple[list[CDM], bool]:
    """Fetch CDMs. Returns (records, is_mock).

    Falls back to mock_cdm_factory on 401 (account lacks CDM access tier).
    Remove fallback once Space-Track CDM access is approved.
    """
    key = f"cdm:limit:{limit}"
    if key in cache:
        cached = cache[key]
        return cached["records"], cached["is_mock"]
    client = _get_client()
    try:
        raw = client.cdm(limit=limit, format="json")
        data = json.loads(raw) if isinstance(raw, str) else raw
        records = [CDM(**row) for row in (data if isinstance(data, list) else [data])]
        is_mock = False
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 401:
            records = mock_cdm_factory(n=limit, seed=42)
            is_mock = True
        else:
            raise
    cache.set(key, {"records": records, "is_mock": is_mock}, expire=1800)
    return records, is_mock
