"""Tiny rich-text layout: *italic* (rust accent), **bold**, \\n for a hard line break.
Used by the carousel, static and reel renderers so headlines mix upright and italic like Steer's brand."""
import re
from dataclasses import dataclass
from .config import BRAND, serif, sans


@dataclass
class Style:
    family: str = "serif"
    size: int = 64
    weight: int = 400
    color: tuple = BRAND["ink"]
    italic_color: tuple = BRAND["rust"]
    line_h: float = 1.15
    align: str = "left"


@dataclass
class Placed:
    x: float
    y: float
    text: str
    font: object
    fill: tuple


def font_for(st, italic, bold):
    if st.family == "serif":
        return serif(st.size, italic, 700 if bold else st.weight)
    return sans(st.size, 700 if bold else st.weight, italic)


def parse(markup):
    out, italic, bold, pending = [], False, False, False
    for part in re.split(r"(\*\*|\*)", markup):
        if part == "**":
            bold = not bold
            continue
        if part == "*":
            italic = not italic
            continue
        for m in re.finditer(r"(\n)|(\s+)|(\S+)", part):
            if m.group(1):
                out.append(("\n", False, False, False))
                pending = False
            elif m.group(2):
                pending = True
            else:
                out.append((m.group(3), italic, bold, pending and bool(out) and out[-1][0] != "\n"))
                pending = False
    return out


def layout(markup, max_w, st):
    words = parse(markup)
    space_w = font_for(st, False, False).getlength(" ")
    lines, cur, cur_w = [], [], 0.0
    for text, it, bd, sp in words:
        if text == "\n":
            lines.append((cur, cur_w))
            cur, cur_w = [], 0.0
            continue
        f = font_for(st, it, bd)
        w = f.getlength(text)
        gap = space_w if (cur and sp) else 0
        if cur and cur_w + gap + w > max_w:
            lines.append((cur, cur_w))
            cur, cur_w, gap = [], 0.0, 0
        cur.append((text, it, bd, f, w, gap))
        cur_w += gap + w
    if cur:
        lines.append((cur, cur_w))
    lh = st.size * st.line_h
    placed = []
    for i, (ws, lw) in enumerate(lines):
        x = {"left": 0, "center": (max_w - lw) / 2, "right": max_w - lw}[st.align]
        base = i * lh + lh * 0.5 + st.size * 0.34
        for text, it, bd, f, w, gap in ws:
            x += gap
            fill = st.italic_color if (it and st.italic_color) else st.color
            placed.append(Placed(x, base, text, f, fill))
            x += w
    return placed, len(lines) * lh
