"""
W1 Monday: Space-Track verification.
Auth, one TLE pull, one CDM pull (falls back to mock when account lacks CDM tier).
Run: uv run python notebooks/spacetrack_verify.py
"""
import httpx
from spacetrack import SpaceTrackClient

from amoa.config import settings
from amoa.data.cdm import CDM, mock_cdm_factory


def verify_auth() -> SpaceTrackClient:
    client = SpaceTrackClient(
        identity=settings.spacetrack_username,
        password=settings.spacetrack_password,
    )
    return client


def pull_tle(client: SpaceTrackClient) -> str:
    """Pull latest GP elements for ISS (NORAD ID 25544). tle_latest retired; use gp."""
    return client.gp(norad_cat_id=25544, orderby="epoch desc", limit=1, format="tle")


def pull_cdm(client: SpaceTrackClient) -> tuple[list[CDM], bool]:
    """Pull one CDM from Space-Track. Returns (records, is_mock).

    Falls back to mock_cdm_factory when account lacks CDM access tier (401).
    Remove the fallback once Space-Track CDM access is approved.
    """
    try:
        raw = client.cdm(limit=1, format="json")
        import json
        data = json.loads(raw) if isinstance(raw, str) else raw
        # Space-Track returns a list of dicts
        records = [CDM(**row) for row in (data if isinstance(data, list) else [data])]
        return records, False
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 401:
            return mock_cdm_factory(n=1, seed=42), True
        raise


if __name__ == "__main__":
    print("Authenticating with Space-Track...")
    client = verify_auth()
    print("[OK] Auth OK")

    print("Pulling TLE for ISS...")
    tle = pull_tle(client)
    print(f"[OK] TLE received:\n{tle[:200]}")

    print("Pulling one CDM...")
    cdms, is_mock = pull_cdm(client)
    source = "[MOCK]" if is_mock else "[LIVE]"
    cdm = cdms[0]
    print(
        f"{source} CDM received:\n"
        f"  TCA           : {cdm.tca.isoformat()}\n"
        f"  Miss distance : {cdm.miss_distance} m\n"
        f"  PC            : {cdm.probability_of_collision:.2e}\n"
        f"  Sat1          : {cdm.sat1_name} ({cdm.sat1_norad_id})\n"
        f"  Sat2          : {cdm.sat2_name} ({cdm.sat2_norad_id})\n"
        f"  Emergency     : {cdm.emergency_reportable}"
    )