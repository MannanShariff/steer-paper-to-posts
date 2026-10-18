"""Brand tokens, canvas sizes and font loading. Every visual decision derives from here."""
from functools import lru_cache
from pathlib import Path
from PIL import ImageFont

ROOT = Path(__file__).resolve().parent.parent


def rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


# Steer brand starter pack
BRAND = {k: rgb(v) for k, v in dict(
    cream="#F5EBDF", rust="#C04E2A", ink="#351D1D",
    clay="#B58777", blush="#E6CBBD", paper="#F8F2EB").items()}
CLAY_TEXT = rgb("#8A5A4A")  # darker clay so small captions stay legible on cream

SIZES = {"feed_4x5": (1080, 1350), "square_1x1": (1080, 1080), "story_9x16": (1080, 1920)}

_SERIF = [
    "/usr/share/fonts/truetype/google-fonts/Lora-Variable.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
]
_SERIF_I = [
    "/usr/share/fonts/truetype/google-fonts/Lora-Italic-Variable.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Italic.ttf",
]
_INTER = "/usr/share/fonts/opentype/inter/Inter-{}.otf"
_SANS_FALLBACK = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
_WEIGHT_NAME = {300: "Light", 400: "Regular", 500: "Medium", 600: "SemiBold", 700: "Bold"}


def _first(paths):
    for p in paths:
        if Path(p).exists():
            return p
    raise FileNotFoundError(paths)


@lru_cache(maxsize=None)
def serif(size, italic=False, weight=400):
    f = ImageFont.truetype(_first(_SERIF_I if italic else _SERIF), int(size))
    try:
        f.set_variation_by_axes([max(400, min(700, weight))])
    except Exception:
        pass
    return f


@lru_cache(maxsize=None)
def sans(size, weight=400, italic=False):
    name = _WEIGHT_NAME.get(weight, "Regular")
    if italic:
        name = "Italic" if name == "Regular" else name + "Italic"
    p = _INTER.format(name)
    if not Path(p).exists():
        p = _SANS_FALLBACK
    return ImageFont.truetype(p, int(size))
