"""
Sentinel-2 GeoTIFF loader — reads, composites to RGB, resizes, base64-encodes for Gemini Vision.

Files expected in data/sentinel/ named S2_{YYYYMMDD}_{BAND}.tiff.
"""
import base64
import re
from io import BytesIO
from pathlib import Path

import numpy as np
import rasterio
from PIL import Image

SENTINEL_DIR = Path("data/sentinel")
_NAME_RE = re.compile(r"S2_(\d{8})_(\w+)\.tiff")


def list_scenes(data_dir: Path = SENTINEL_DIR) -> list[Path]:
    """Return sorted list of S2_*.tiff paths in data_dir."""
    return sorted(data_dir.glob("S2_*.tiff"))


def load_scene(path: Path, max_px: int = 512) -> dict:
    """
    Read a GeoTIFF, composite to RGB uint8, resize to max_px on longest side.

    Returns dict with filename, date, band, original dims, resized dims, base64_image.
    """
    with rasterio.open(path) as src:
        original_width = src.width
        original_height = src.height
        count = src.count

        if count >= 3:
            r = src.read(1).astype(np.float32)
            g = src.read(2).astype(np.float32)
            b = src.read(3).astype(np.float32)
            rgb = np.stack([r, g, b], axis=-1)
        else:
            band = src.read(1).astype(np.float32)
            rgb = np.stack([band, band, band], axis=-1)

    vmin, vmax = rgb.min(), rgb.max()
    if vmax > vmin:
        rgb = (rgb - vmin) / (vmax - vmin) * 255.0
    rgb = rgb.clip(0, 255).astype(np.uint8)

    img = Image.fromarray(rgb, mode="RGB")

    scale = min(max_px / img.width, max_px / img.height, 1.0)
    if scale < 1.0:
        new_w = max(1, int(img.width * scale))
        new_h = max(1, int(img.height * scale))
        img = img.resize((new_w, new_h), Image.LANCZOS)

    buf = BytesIO()
    img.save(buf, format="JPEG", quality=85)
    b64 = base64.b64encode(buf.getvalue()).decode("utf-8")

    m = _NAME_RE.match(path.name)
    date = m.group(1) if m else "unknown"
    band = m.group(2) if m else "unknown"

    return {
        "filename": path.name,
        "date": date,
        "band": band,
        "original_width": original_width,
        "original_height": original_height,
        "resized_width": img.width,
        "resized_height": img.height,
        "base64_image": b64,
    }
