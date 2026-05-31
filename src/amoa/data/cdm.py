"""Mock CDM (Conjunction Data Message) factory.

Mirrors the field subset returned by Space-Track /class/cdm/.
Used as fallback when account lacks CDM access tier.

Real CDM docs: https://www.space-track.org/documentation#/conjunctions
"""
import random
from datetime import UTC, datetime, timedelta

from pydantic import BaseModel, Field


class CDM(BaseModel):
    """Subset of Space-Track CDM fields relevant to Safety Pilot."""

    cdm_id: int
    created: datetime
    tca: datetime                        # Time of Closest Approach (UTC)
    miss_distance: float                 # metres
    probability_of_collision: float      # 0..1
    relative_speed: float                # m/s at TCA

    # Radial / In-track / Cross-track components (metres)
    relative_position_r: float
    relative_position_t: float
    relative_position_n: float

    sat1_norad_id: int
    sat1_name: str
    sat1_object_type: str                # PAYLOAD | DEBRIS | ROCKET BODY | UNKNOWN

    sat2_norad_id: int
    sat2_name: str
    sat2_object_type: str

    emergency_reportable: bool = False


_DEBRIS_NAMES = [
    "COSMOS 2251 DEB", "FENGYUN 1C DEB", "SL-16 R/B", "IRIDIUM 33 DEB",
    "DELTA 4 R/B", "ARIANE 44L R/B", "SL-8 R/B", "COSMOS 1408 DEB",
]

_PAYLOAD_NAMES = [
    "ISS (ZARYA)", "STARLINK-1234", "TERRA", "AQUA", "SENTINEL-2A",
    "LANDSAT 9", "NOAA 20", "JPSS-1",
]

_OBJECT_TYPES = ["PAYLOAD", "DEBRIS", "ROCKET BODY", "UNKNOWN"]


def mock_cdm_factory(n: int = 5, seed: int | None = None) -> list[CDM]:
    """Return n mock CDMs with physically plausible values.

    Miss distances 50–9 000 m, PC range 1e-8 to 5e-3,
    TCA within next 7 days from call time.
    """
    rng = random.Random(seed)
    now = datetime.now(UTC)
    records: list[CDM] = []

    for i in range(n):
        miss_dist = rng.uniform(50, 9_000)          # metres
        # PC rough log-uniform so we get realistic spread
        log_pc = rng.uniform(-8, -2.3)
        pc = 10 ** log_pc

        r = rng.uniform(-miss_dist, miss_dist)
        t = rng.uniform(-miss_dist, miss_dist)
        # N makes up remainder so vector norm ≈ miss_dist
        n_comp = (miss_dist**2 - r**2 - t**2) ** 0.5 * rng.choice([-1, 1])

        records.append(CDM(
            cdm_id=100_000 + i,
            created=now - timedelta(hours=rng.uniform(0, 12)),
            tca=now + timedelta(hours=rng.uniform(1, 168)),
            miss_distance=round(miss_dist, 1),
            probability_of_collision=round(pc, 12),
            relative_speed=round(rng.uniform(100, 15_000), 2),
            relative_position_r=round(r, 1),
            relative_position_t=round(t, 1),
            relative_position_n=round(n_comp, 1),
            sat1_norad_id=rng.choice([25544, 48274, 43013, 39084]),
            sat1_name=rng.choice(_PAYLOAD_NAMES),
            sat1_object_type="PAYLOAD",
            sat2_norad_id=rng.randint(10_000, 55_000),
            sat2_name=rng.choice(_DEBRIS_NAMES),
            sat2_object_type=rng.choice(_OBJECT_TYPES),
            emergency_reportable=pc > 1e-4,
        ))

    return records
