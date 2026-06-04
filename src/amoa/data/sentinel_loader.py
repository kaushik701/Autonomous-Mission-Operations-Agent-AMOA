"""
Sentinel-2 imagery loader.
Reads GeoTIFF, resizes to model-friendly dimensions, base64-encodes for vision API.
"""
import base64
from pathlib import Path

import numpy as np
from PIL import Image

SENTINEL_DIR = Path(__file__).parent.parent.parent.parent / "data" / "sentinel"
TARGET_SIZE = (512, 512)


def load_scene(filename: str) -> dict:
    """
    Load one Sentinel-2 scene from data/sentinel/.

    Returns dict with:
        - filename: str
        - base64_image: str (for vision API)
        - width, height: int (original dimensions)
        - bands: int (number of spectral bands)
    """
    path = SENTINEL_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"Scene not found: {path}")

    img = Image.open(path)
    original_size = img.size
    bands = len(img.getbands())

    # Resize for vision API — keep aspect ratio
    img_resized = img.resize(TARGET_SIZE, Image.LANCZOS)

    # Convert to RGB if needed (Sentinel-2 can be multi-band)
    if img_resized.mode not in ("RGB", "L"):
        img_resized = img_resized.convert("RGB")

    # Base64 encode
    import io
    buffer = io.BytesIO()
    img_resized.save(buffer, format="JPEG", quality=85)
    b64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

    return {
        "filename": filename,
        "base64_image": b64,
        "original_width": original_size[0],
        "original_height": original_size[1],
        "bands": bands,
    }


def list_scenes() -> list[str]:
    """Return GeoTIFF filenames in data/sentinel/, TCI files first."""
    all_files = sorted(SENTINEL_DIR.glob("*.tif*"))
    tci = [f.name for f in all_files if "TCI" in f.name]
    other = [f.name for f in all_files if "TCI" not in f.name]
    return tci + other