from __future__ import annotations

from typing import Dict, List, Tuple

from colorthief import ColorThief


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

