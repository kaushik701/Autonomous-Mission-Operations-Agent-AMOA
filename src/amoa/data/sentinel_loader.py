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
    path = SENTINEL_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"Scene not found: {path}")

    img = Image.open(path)
    original_size = img.size
    bands = len(img.getbands())

    # Resize
    img_resized = img.resize(TARGET_SIZE, Image.LANCZOS)

    # Always convert to RGB — handles single-band, palette, RGBA
    img_rgb = img_resized.convert("RGB")

    import io
    buffer = io.BytesIO()
    img_rgb.save(buffer, format="JPEG", quality=85)
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