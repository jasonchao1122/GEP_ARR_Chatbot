from __future__ import annotations

from typing import Dict, List, Tuple
from io import BytesIO

from colorthief import ColorThief
from PIL import Image

try:
    import fitz  # PyMuPDF
except Exception:  # pragma: no cover - optional if PDF not needed
    fitz = None  # type: ignore


def _rgb_to_hex(rgb: Tuple[int, int, int]) -> str:
    r, g, b = rgb
    return f"#{r:02x}{g:02x}{b:02x}"


def extract_palette(file_obj, color_count: int = 6) -> List[str]:
    """Extract a color palette from an image file-like object using ColorThief.

    Returns a list of hex color strings sorted by prominence.
    """
    try:
        file_obj.seek(0)
    except Exception:
        pass
    thief = ColorThief(file_obj)
    palette = thief.get_palette(color_count=color_count)
    return [_rgb_to_hex(c) for c in palette]


def extract_palette_from_pil(image: Image.Image, color_count: int = 6) -> List[str]:
    buf = BytesIO()
    # Use JPEG to compress; fallback to PNG if RGBA
    mode = image.mode
    save_format = "PNG" if (mode == "RGBA" or mode == "LA") else "JPEG"
    image.save(buf, format=save_format)
    buf.seek(0)
    return extract_palette(buf, color_count=color_count)


def pdf_to_images(file_obj, max_pages: int = 4, zoom: float = 2.0) -> List[Image.Image]:
    """Render first N pages of a PDF into PIL Images using PyMuPDF.

    Returns empty list if PyMuPDF is unavailable.
    """
    if fitz is None:
        return []
    try:
        # Read bytes and open via stream to avoid file system
        try:
            file_obj.seek(0)
        except Exception:
            pass
        pdf_bytes = file_obj.read()
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    except Exception:
        return []

    images: List[Image.Image] = []
    try:
        for i, page in enumerate(doc):
            if i >= max_pages:
                break
            mat = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat, alpha=False)
            mode = "RGBA" if pix.alpha else "RGB"
            img = Image.frombytes(mode, (pix.width, pix.height), pix.samples)
            images.append(img)
    finally:
        doc.close()
    return images


def get_default_theme() -> Dict[str, str]:
    return {
        "actual": "#ff7f0e",  # orange
        "plan": "#1f77b4",    # blue
        "positive": "#2ca02c",  # green
        "negative": "#d62728",  # red
        "neutral": "#7f7f7f",   # gray
    }


def infer_theme_from_palette(palette: List[str]) -> Dict[str, str]:
    """Heuristically map palette colors to theme roles.

    This is intentionally simple; users can override via color pickers.
    """
    defaults = get_default_theme()
    if not palette:
        return defaults

    # Start with defaults, then try to override with palette entries
    theme = dict(defaults)
    # Assign dominant color to actual, second to plan when available
    if len(palette) >= 1:
        theme["actual"] = palette[0]
    if len(palette) >= 2:
        theme["plan"] = palette[1]
    # Try to find greenish and reddish tones for positive/negative
    def hex_to_rgb(h: str) -> Tuple[int, int, int]:
        h = h.lstrip('#')
        return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))  # type: ignore

    def score_red(rgb: Tuple[int, int, int]) -> int:
        r, g, b = rgb
        return r - max(g, b)

    def score_green(rgb: Tuple[int, int, int]) -> int:
        r, g, b = rgb
        return g - max(r, b)

    rgbs = [hex_to_rgb(c) for c in palette]
    if rgbs:
        green_candidate = max(rgbs, key=score_green)
        red_candidate = max(rgbs, key=score_red)
        theme["positive"] = _rgb_to_hex(green_candidate)
        theme["negative"] = _rgb_to_hex(red_candidate)

    return theme

