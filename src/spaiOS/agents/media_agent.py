"""PIL/numpy image processing agent — photo filters and basic transforms."""

from pathlib import Path

import numpy as np
from PIL import Image, ImageEnhance

_SUPPORTED_STYLES = {"90s_film", "vintage", "high_contrast", "black_white"}


def _output_path(image_path: str, style: str) -> str:
    p = Path(image_path)
    return str(p.parent / f"{p.stem}_{style}.jpg")


def _to_rgb(img: Image.Image) -> Image.Image:
    if img.mode != "RGB":
        return img.convert("RGB")
    return img


def _apply_black_white(img: Image.Image) -> Image.Image:
    return img.convert("L").convert("RGB")


def _apply_high_contrast(img: Image.Image) -> Image.Image:
    return ImageEnhance.Contrast(img).enhance(2.0)


def _apply_vintage(img: Image.Image) -> Image.Image:
    # Partial desaturation (50%) then warm tint
    desaturated = ImageEnhance.Color(img).enhance(0.5)
    arr = np.array(desaturated, dtype=np.float32)
    arr[:, :, 0] = np.clip(arr[:, :, 0] * 1.15, 0, 255)  # warm red boost
    arr[:, :, 2] = np.clip(arr[:, :, 2] * 0.80, 0, 255)  # cool blue reduction
    return Image.fromarray(arr.astype(np.uint8))


def _apply_90s_film(img: Image.Image) -> Image.Image:
    w, h = img.size

    # 20% desaturation
    partly_desat = ImageEnhance.Color(img).enhance(0.8)

    # Warm color shift
    arr = np.array(partly_desat, dtype=np.float32)
    arr[:, :, 0] = np.clip(arr[:, :, 0] * 1.10, 0, 255)
    arr[:, :, 2] = np.clip(arr[:, :, 2] * 0.85, 0, 255)

    # Film grain
    rng = np.random.default_rng(seed=42)
    grain = rng.normal(loc=0, scale=12.0, size=(h, w, 3))
    arr = np.clip(arr + grain, 0, 255)

    # Vignette
    y_idx, x_idx = np.mgrid[0:h, 0:w]
    cy, cx = h / 2, w / 2
    dist = np.sqrt(((x_idx - cx) / cx) ** 2 + ((y_idx - cy) / cy) ** 2)
    vignette = np.clip(1.0 - dist * 0.6, 0, 1)
    arr = np.clip(arr * vignette[:, :, np.newaxis], 0, 255)

    return Image.fromarray(arr.astype(np.uint8))


_FILTER_FNS = {
    "black_white": _apply_black_white,
    "high_contrast": _apply_high_contrast,
    "vintage": _apply_vintage,
    "90s_film": _apply_90s_film,
}


class MediaAgent:
    def apply_filter(self, image_path: str, style: str) -> str:
        """Apply a named filter to an image and save the result. Returns output path."""
        if style not in _SUPPORTED_STYLES:
            raise ValueError(
                f"Unknown style '{style}'. Choose from: {sorted(_SUPPORTED_STYLES)}"
            )

        p = Path(image_path)
        if not p.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")

        img = _to_rgb(Image.open(p))
        result = _FILTER_FNS[style](img)

        out = _output_path(image_path, style)
        result.save(out, format="JPEG", quality=92)
        return out

    def get_image_info(self, path: str) -> dict:
        """Return basic metadata for an image file."""
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(f"Image not found: {path}")
        with Image.open(p) as img:
            return {
                "width": img.width,
                "height": img.height,
                "mode": img.mode,
                "format": img.format,
                "size_bytes": p.stat().st_size,
            }

    def resize_image(self, path: str, width: int, height: int) -> str:
        """Resize image to given dimensions using Lanczos resampling. Returns output path."""
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(f"Image not found: {path}")
        img = _to_rgb(Image.open(p))
        resized = img.resize((width, height), Image.Resampling.LANCZOS)
        out = str(p.parent / f"{p.stem}_resized_{width}x{height}.jpg")
        resized.save(out, format="JPEG", quality=92)
        return out
