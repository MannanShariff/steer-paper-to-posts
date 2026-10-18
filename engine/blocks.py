"""Visual building blocks shared by carousel, static and reel renderers.

Every block knows its height and how to draw itself at time t (seconds since the block
started). A static post draws every block at t = infinity (final state); a reel draws the
same blocks frame by frame, so the carousel and the reel can never drift apart visually."""
import math
from PIL import Image, ImageDraw
from .config import BRAND, CLAY_TEXT, serif, sans
from .richtext import Style, layout

INF = 1e9


def ease(t):
    t = max(0.0, min(1.0, t))
    return 1 - (1 - t) ** 3


# ---------- antialiased primitives ----------
def _mask(size, fn, ss=3):
    w, h = size
    m = Image.new("L", (max(1, w * ss), max(1, h * ss)), 0)
    fn(ImageDraw.Draw(m), ss)
    return m.resize((max(1, w), max(1, h)), Image.LANCZOS)


def _paste(img, color, mask, xy, alpha=1.0):
    if alpha < 1:
        mask = mask.point(lambda v: int(v * alpha))
    img.paste(Image.new("RGB", mask.size, color), (int(xy[0]), int(xy[1])), mask)


def round_rect(img, box, r, color, alpha=1.0):
    x0, y0, x1, y1 = [int(round(v)) for v in box]
    w, h = max(1, x1 - x0), max(1, y1 - y0)
    r = int(min(r, w // 2, h // 2))
    m = _mask((w, h), lambda d, s: d.rounded_rectangle((0, 0, w * s - 1, h * s - 1), r * s, fill=255))
    _paste(img, color, m, (x0, y0), alpha)


def circle(img, cx, cy, r, color, alpha=1.0, ring=0):
    d = int(2 * r)
    def fn(dr, s):
        dr.ellipse((0, 0, d * s - 1, d * s - 1), fill=255)
        if ring:
            dr.ellipse((ring * s, ring * s, (d - ring) * s - 1, (d - ring) * s - 1), fill=0)
    _paste(img, color, _mask((d, d), fn), (cx - r, cy - r), alpha)


def text_a(img, xy, text, font, fill, alpha=1.0, anchor="ls"):
    if alpha >= 0.995:
        ImageDraw.Draw(img).text(xy, text, font=font, fill=fill, anchor=anchor)
        return
    if alpha <= 0.01:
        return
    l, t, r, b = font.getbbox(text, anchor=anchor)
    pad = 4
    w, h = int(r - l + 2 * pad), int(b - t + 2 * pad)
    layer = Image.new("L", (w, h), 0)
    ImageDraw.Draw(layer).text((-l + pad, -t + pad), text, font=font, fill=int(255 * alpha), anchor=anchor)
    img.paste(Image.new("RGB", (w, h), fill), (int(xy[0] + l - pad), int(xy[1] + t - pad)), layer)


# ---------- blocks ----------
class Block:
    height = 0
    dur = 0.6

    def draw(self, img, x, y, t=INF):
        raise NotImplementedError


class Gap(Block):
    def __init__(self, h):
        self.height, self.dur = h, 0

    def draw(self, img, x, y, t=INF):
        pass


class TextBlock(Block):
    def __init__(self, markup, style, width, stagger=0.05, dur=0.45, rise=22):
        self.placed, self.height = layout(markup, width, style)
        self.stagger, self._d, self.rise = stagger, dur, rise
        self.dur = len(self.placed) * stagger + dur

    def draw(self, img, x, y, t=INF):
        for i, p in enumerate(self.placed):
            a = ease((t - i * self.stagger) / self._d)
            if a > 0:
                text_a(img, (x + p.x, y + p.y + (1 - a) * self.rise), p.text, p.font, p.fill, a)


class Eyebrow(Block):
    def __init__(self, text, size=26, tracking=3):
        self.text, self.size, self.tr = text.lower(), size, tracking
        self.font = sans(size, 500)
        self.height, self.dur = size * 1.6, 0.5

    def draw(self, img, x, y, t=INF):
        a = ease(t / 0.5)
        cx = x
        for ch in self.text:
            text_a(img, (cx, y + self.size * 1.05), ch, self.font, CLAY_TEXT, a)
            cx += self.font.getlength(ch) + self.tr


class Stat(Block):
    """One giant figure, auto-fitted to the width."""
    def __init__(self, text, width, size=230, color=BRAND["rust"], italic=True):
        s = size
        while serif(s, italic, 400).getlength(text) > width and s > 60:
            s -= 6
        self.font, self.text, self.color, self.size = serif(s, italic, 400), text, color, s
        self.height, self.dur = s * 1.05, 0.8

    def draw(self, img, x, y, t=INF):
        a = ease(t / 0.7)
        text_a(img, (x, y + self.size * 0.88 + (1 - a) * 30), self.text, self.font, self.color, a)


class Duo(Block):
    """Two figures side by side with captions (e.g. waist flags for women and men)."""
    def __init__(self, items, width):
        self.items, self.width = items, width
        self.col = width / len(items)
        self.fs = 126
        self.height, self.dur = self.fs * 1.0 + 80, 1.2
        self.cap = sans(30, 500)

    def draw(self, img, x, y, t=INF):
        for i, (big, cap) in enumerate(self.items):
            a = ease((t - i * 0.35) / 0.7)
            cx = x + i * self.col
            text_a(img, (cx, y + self.fs * 0.85 + (1 - a) * 26), big, serif(self.fs, True, 400), BRAND["rust"], a)
            text_a(img, (cx + 4, y + self.fs * 0.85 + 52), cap, self.cap, BRAND["ink"], a)


class Bars(Block):
    def __init__(self, items, width, bar_h=40):
        self.items, self.width, self.bh = items, width, bar_h
        self.row = 34 + 14 + bar_h + 40
        self.height = self.row * len(items) - 40
        self.dur = 0.4 * len(items) + 1.3
        self.lf, self.vf = sans(30, 500), sans(34, 700)

    def draw(self, img, x, y, t=INF):
        for i, it in enumerate(self.items):
            ry = y + i * self.row
            la = ease((t - i * 0.4) / 0.4)
            text_a(img, (x, ry + 28), it["label"], self.lf, BRAND["ink"], la)
            text_a(img, (x + self.width, ry + 30), it["display"], self.vf, it.get("color", BRAND["rust"]), la, anchor="rs")
            by = ry + 34 + 14
            round_rect(img, (x, by, x + self.width, by + self.bh), self.bh // 2, BRAND["blush"], la)
            frac = ease((t - i * 0.4 - 0.25) / 1.0) * (it["value"] / it["max"])
            if frac > 0.004:
                round_rect(img, (x, by, x + max(self.bh, self.width * frac), by + self.bh), self.bh // 2, it.get("color", BRAND["rust"]))


class NumberLine(Block):
    """Two BMI scales stacked: usual cut-offs vs Asian Indian cut-offs."""
    def __init__(self, rows, width, lo=20, hi=32, ticks=(23, 25, 30)):
        self.rows, self.width, self.lo, self.hi, self.ticks = rows, width, lo, hi, ticks
        self.rh = 64
        self.row_gap = 64 + 22
        self.height = len(rows) * (self.rh + self.row_gap) + 20
        self.dur = len(rows) * 0.7 + 1.4
        self.lf, self.sf, self.tf = sans(30, 600), sans(24, 600), sans(30, 700)

    def _x(self, v):
        return (v - self.lo) / (self.hi - self.lo) * self.width

    def draw(self, img, x, y, t=INF):
        for r, row in enumerate(self.rows):
            ry = y + r * (self.rh + self.row_gap)
            la = ease((t - r * 0.7) / 0.4)
            text_a(img, (x, ry + 26), row["label"], self.lf, BRAND["ink"], la)
            by = ry + 44
            prog = ease((t - r * 0.7 - 0.2) / 1.1)
            full = int(self.width)
            strip = Image.new("RGB", (full, self.rh), BRAND["blush"])
            sd = ImageDraw.Draw(strip)
            for a, b, col, name in row["segments"]:
                x0, x1 = self._x(max(a, self.lo)), self._x(min(b, self.hi))
                sd.rectangle((x0, 0, x1, self.rh), fill=col)
                if x1 - x0 > 120 and name:
                    lab = BRAND["ink"] if col == BRAND["clay"] else BRAND["cream"]
                    sd.text(((x0 + x1) / 2, self.rh / 2), name, font=self.sf, fill=lab, anchor="mm")
            mw = int(full * prog)
            if mw > 6 and la > 0.01:
                m = _mask((mw, self.rh), lambda d, s: d.rounded_rectangle((0, 0, mw * s - 1, self.rh * s - 1), 14 * s, fill=255))
                img.paste(strip.crop((0, 0, mw, self.rh)), (int(x), int(by)), m)
        ty = y + len(self.rows) * (self.rh + self.row_gap) - self.row_gap + 44 + 18
        a = ease((t - len(self.rows) * 0.7 - 0.6) / 0.5)
        d = ImageDraw.Draw(img)
        for v in self.ticks:
            tx = x + self._x(v)
            text_a(img, (tx, ty + 14), f"{v}", self.tf, BRAND["ink"], a, anchor="ms")


class Bullets(Block):
    def __init__(self, lines, width, size=38):
        st = Style("sans", size, 400, BRAND["ink"], BRAND["rust"], 1.35)
        self.items = [TextBlock(s, st, width - 56, stagger=0.03, dur=0.4, rise=14) for s in lines]
        self.gap = 30
        self.height = sum(b.height for b in self.items) + self.gap * (len(self.items) - 1)
        self.dur = len(self.items) * 0.9 + 0.6

    def draw(self, img, x, y, t=INF):
        cy = y
        for i, b in enumerate(self.items):
            tt = t - i * 0.9
            a = ease(tt / 0.4)
            if a > 0:
                circle(img, x + 12, cy + 24, 8, BRAND["rust"], a)
                b.draw(img, x + 56, cy, tt)
            cy += b.height + self.gap


class Pill(Block):
    def __init__(self, text, size=34):
        self.font = sans(size, 700)
        self.text = text
        self.w = int(self.font.getlength(text) + 96)
        self.h = int(size * 2.3)
        self.height, self.dur = self.h, 0.7

    def draw(self, img, x, y, t=INF):
        a = ease(t / 0.5)
        round_rect(img, (x, y + (1 - a) * 14, x + self.w, y + (1 - a) * 14 + self.h), self.h // 2, BRAND["rust"], a)
        text_a(img, (x + self.w / 2, y + self.h / 2 + (1 - a) * 14), self.text, self.font, BRAND["cream"], a, anchor="mm")


# ---------- flow ----------
def total_height(blocks):
    return sum(b.height for b in blocks)


def place(blocks, top, bottom, anchor=0.42):
    """Return [(block, y)] with the stack centred (biased up) inside [top, bottom]."""
    total = total_height(blocks)
    y = top + max(0, (bottom - top - total)) * anchor
    out = []
    for b in blocks:
        out.append((b, y))
        y += b.height
    return out
