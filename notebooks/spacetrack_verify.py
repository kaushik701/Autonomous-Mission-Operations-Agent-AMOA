"""
W1 Monday: Space-Track verification.
Auth, one TLE pull, one CDM pull.
Run: uv run python notebooks/spacetrack_verify.py
"""
import asyncio
from spacetrack import SpaceTrackClient
from amoa.config import settings


def verify_auth():
    client = SpaceTrackClient(
        identity=settings.spacetrack_username,
        password=settings.spacetrack_password,
    )
    return client


def pull_tle(client: SpaceTrackClient):
    """Pull latest GP elements for ISS (NORAD ID 25544). tle_latest retired; use gp."""
    tle = client.gp(norad_cat_id=25544, orderby="epoch desc", limit=1, format="tle")
    return tle


def pull_cdm(client: SpaceTrackClient):
    """Pull one recent CDM."""
    cdm = client.cdm(limit=1, format="json")
    return cdm


if __name__ == "__main__":
    print("Authenticating with Space-Track...")
    client = verify_auth()
    print("[OK] Auth OK")

    print("Pulling TLE for ISS...")
    tle = pull_tle(client)
    print(f"[OK] TLE received:\n{tle[:200]}")

    print("Pulling one CDM...")
    cdm = pull_cdm(client)
    print(f"[OK] CDM received:\n{str(cdm)[:200]}")