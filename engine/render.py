"""Slide renderer. One function turns a slide spec into pixels at any canvas size and any animation time,
so the carousel, the static post, its 1:1 resize and the reel scenes all come from the same code."""
from dataclasses import dataclass
from PIL import Image, ImageDraw
from .config import BRAND, CLAY_TEXT, serif, sans
from .richtext import Style
from . import blocks as B

MODES = {  # name: (W, H, header_y, content_top, rule_y, footer_base)
    "feed":   (1080, 1350, 84, 270, 1195, 1268),
    "square": (1080, 1080, 70, 220, 935, 1008),
    "story":  (1080, 1920, 230, 380, 1315, 1372),
}
SEG = {"clay": BRAND["clay"], "rust": BRAND["rust"], "ink": BRAND["ink"], "blush": BRAND["blush"]}
MARGIN = 90


@dataclass
class Built:
    mode: str
    W: int
    H: int
    placed: list
    slide: dict
    tag: str
    idx: int
    total: int
    dur: float


def _style(size, family="serif", weight=400, color=None, lh=1.12, align="left"):
    return Style(family, int(size), weight, color or BRAND["ink"], BRAND["rust"], lh, align)


def _blocks(slide, width, s, mode):
    t = slide["type"]
    out = []
    eb = slide.get("eyebrow")
    if eb:
        out += [B.Eyebrow(eb), B.Gap(16)]
    h = slide.get("headline", "")
    if t == "cover":
        out += [B.TextBlock(h, _style(112 * s, lh=1.02), width), B.Gap(40)]
        if slide.get("sub"):
            out.append(B.TextBlock(slide["sub"], _style(40, "sans", 400, CLAY_TEXT, 1.4), width))
    elif t == "stat":
        out += [B.Stat(slide["stat"], width, size=250 * s), B.Gap(24), B.TextBlock(h, _style(60 * s, lh=1.15), width)]
    elif t == "statement":
        out += [B.TextBlock(h, _style(100 * s, lh=1.04), width), B.Gap(40)]
        if slide.get("body"):
            out.append(B.TextBlock(slide["body"], _style(42, "sans", 400, BRAND["ink"], 1.4), width))
    elif t == "bars":
        out += [B.TextBlock(h, _style(70 * s, lh=1.08), width), B.Gap(52), B.Bars(slide["items"], width)]
        if slide.get("note"):
            out += [B.Gap(30), B.TextBlock(slide["note"], _style(30, "sans", 400, CLAY_TEXT, 1.35), width)]
    elif t == "numberline":
        rows = [{"label": r["label"], "segments": [(a, b, SEG[c], n) for a, b, c, n in r["segments"]]} for r in slide["rows"]]
        out += [B.TextBlock(h, _style(70 * s, lh=1.08), width), B.Gap(34), B.NumberLine(rows, width, ticks=tuple(slide.get("ticks", (23, 25, 30))))]
        if slide.get("note"):
            out += [B.Gap(14), B.TextBlock(slide["note"], _style(28, "sans", 400, CLAY_TEXT, 1.35), width)]
    elif t == "duo":
        out += [B.TextBlock(h, _style(78 * s, lh=1.08), width), B.Gap(40), B.Duo([tuple(i) for i in slide["items"]], width)]
        if slide.get("note"):
            out += [B.Gap(30), B.TextBlock(slide["note"], _style(32, "sans", 400, CLAY_TEXT, 1.4), width)]
    elif t == "bullets":
        out += [B.TextBlock(h, _style(78 * s, lh=1.08), width), B.Gap(44), B.Bullets(slide["lines"], width, size=int(38 * max(s, .85)))]
    elif t == "cta":
        out += [B.TextBlock(h, _style(96 * s, lh=1.04), width), B.Gap(46), B.Pill(slide["pill"]), B.Gap(30)]
        if slide.get("small"):
            out.append(B.TextBlock(slide["small"], _style(34, "sans", 400, CLAY_TEXT, 1.4), width))
        out += [B.Gap(40), B.TextBlock("steerclub.com", _style(54, "serif", 400, BRAND["rust"], 1.1), width)]
    else:
        raise ValueError(f"unknown slide type {t}")
    return out


def build(slide, mode="feed", tag="", idx=0, total=0):
    W, H, hy, top, rule, fb = MODES[mode]
    width = W - 2 * MARGIN
    bottom = rule - 50
    for s in ((1.3, 1.15, 1.0, .9, .8, .7, .6) if mode == "story" else (1.0, .9, .8, .7, .6)):
        bl = _blocks(slide, width, s, mode)
        if B.total_height(bl) <= bottom - top or s == .6:
            break
    placed = B.place(bl, top, bottom, anchor=0.38)
    dur = max([b.dur for b in bl] + [0.5])
    return Built(mode, W, H, placed, slide, tag, idx, total, dur)


def draw(b, t=B.INF, bg=None, chrome=True):
    W, H, hy, top, rule, fb = MODES[b.mode]
    img = bg.copy() if bg is not None else Image.new("RGB", (W, H), BRAND["cream"])
    d = ImageDraw.Draw(img)
    if chrome:
        d.text((MARGIN, hy + 50), "steer", font=serif(62, False, 600), fill=BRAND["rust"], anchor="ls")
        if b.total and b.mode != "story":
            d.text((W - MARGIN, hy + 46), f"{b.idx} / {b.total}", font=sans(26, 500), fill=CLAY_TEXT, anchor="rs")
        d.line((MARGIN, rule, W - MARGIN, rule), fill=BRAND["blush"], width=2)
        s = b.slide
        label = ""
        if s["type"] == "cta":
            label = ""
        elif s.get("claims"):
            label = "Source: " + b.tag
        elif s.get("steer_view"):
            label = "Steer's view, not a study finding"
        if label:
            d.text((MARGIN, fb), label, font=sans(24, 400), fill=CLAY_TEXT, anchor="ls")
        d.text((W - MARGIN, fb), "steerclub.com", font=sans(26, 600), fill=BRAND["rust"], anchor="rs")
    for blk, y in b.placed:
        blk.draw(img, MARGIN, y, t)
    return img
