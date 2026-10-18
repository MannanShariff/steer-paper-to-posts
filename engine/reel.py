"""Reel renderer: scenes -> frames -> mp4 with voiceover and burned-in subtitles.
Voice: ffmpeg's built-in flite engine (offline placeholder). Swap `synth()` for a production TTS (ElevenLabs, Sarvam, Azure)
without touching anything else."""
import subprocess, wave, tempfile, os, math, time
from pathlib import Path
from PIL import Image, ImageDraw
from .config import BRAND, CLAY_TEXT, serif, sans
from . import render as R
from . import blocks as B

FPS = 24
PAD_BEFORE, PAD_AFTER, MIN_HOLD = 0.35, 0.55, 1.2


def synth(text, path, voice="slt"):
    """Text -> 44.1 kHz mono wav. Returns duration in seconds."""
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as f:
        f.write(text)
        tf = f.name
    try:
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i",
                        f"flite=textfile={tf}:voice={voice}", "-ar", "44100", "-ac", "1", path], check=True)
    finally:
        os.unlink(tf)
    with wave.open(path) as w:
        return w.getnframes() / w.getframerate()


def _join_wavs(parts, out):
    """parts: list of ('sil', seconds) | ('wav', path)."""
    rate = 44100
    with wave.open(out, "wb") as o:
        o.setnchannels(1); o.setsampwidth(2); o.setframerate(rate)
        for kind, v in parts:
            if kind == "sil":
                o.writeframes(b"\x00\x00" * int(rate * v))
            else:
                with wave.open(v) as w:
                    o.writeframes(w.readframes(w.getnframes()))


def _wrap(text, font, max_w):
    words, lines, cur = text.split(), [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if font.getlength(trial) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur); cur = w
    if cur:
        lines.append(cur)
    return lines


def _subtitle(img, text, prog, y_top=1430, max_w=900):
    """Karaoke-style: spoken words ink, current word rust, upcoming clay. prog in 0..1."""
    font = sans(46, 700)
    lines = _wrap(text, font, max_w)
    n = sum(len(l.split()) for l in lines)
    cur = min(n - 1, int(prog * n)) if prog < 1 else n  # n means all spoken
    lh = 66
    box_h = len(lines) * lh + 36
    B.round_rect(img, (90 - 20, y_top - 18, 1080 - 90 + 20, y_top - 18 + box_h), 28, BRAND["paper"])
    d = ImageDraw.Draw(img)
    k = 0
    for li, line in enumerate(lines):
        x = (1080 - font.getlength(line)) / 2
        y = y_top + li * lh + 48
        for w in line.split():
            col = BRAND["ink"] if k < cur else (BRAND["rust"] if k == cur else BRAND["clay"])
            d.text((x, y), w, font=font, fill=col, anchor="ls")
            x += font.getlength(w + " ")
            k += 1


def render_reel(spec, out_mp4, tag, work, log=print):
    work = Path(work); work.mkdir(parents=True, exist_ok=True)
    scenes = spec["reel"]["scenes"]
    t0 = time.time()
    parts, plan = [], []
    for i, sc in enumerate(scenes, 1):
        wp = str(work / f"line{i}.wav")
        sp = synth(sc["say"], wp)
        built = R.build(sc["slide"], "story", tag, i, len(scenes))
        dur = max(PAD_BEFORE + sp + PAD_AFTER, built.dur + 0.9, MIN_HOLD)
        parts += [("sil", PAD_BEFORE), ("wav", wp), ("sil", dur - PAD_BEFORE - sp)]
        plan.append((sc, built, dur, sp))
    audio = str(work / "voice.wav")
    _join_wavs(parts, audio)
    total = sum(p[2] for p in plan)
    log(f"  reel: {len(scenes)} scenes, {total:.1f}s, voiceover synthesised in {time.time()-t0:.1f}s")
    bg = Image.new("RGB", (1080, 1920), BRAND["cream"])
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "1080x1920", "-r", str(FPS), "-i", "-",
           "-i", audio, "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k",
           "-movflags", "+faststart", "-shortest", str(out_mp4)]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    t_start, poster = 0.0, None
    for si, (sc, built, dur, sp) in enumerate(plan):
        nframes = int(round(dur * FPS))
        cache = {}
        for f in range(nframes):
            t = f / FPS
            tt = min(t, built.dur + 0.05)
            sub_prog = (t - PAD_BEFORE) / max(sp, 0.1)
            sub_prog = max(0.0, min(1.0, sub_prog))
            widx = int(sub_prog * 1000) // 40  # quantise so identical frames are reused
            key = (round(tt, 2), widx)
            if key not in cache:
                img = R.draw(built, tt, bg)
                gprog = (t_start + t) / total
                B.round_rect(img, (0, 196, int(1080 * gprog), 202), 3, BRAND["rust"])
                _subtitle(img, sc["sub"], sub_prog if sub_prog < 1 else 1.0)
                cache[key] = img.tobytes()
                if poster is None and si == 1 and t > built.dur * 0.9:
                    poster = img.copy()
            p.stdin.write(cache[key])
        t_start += dur
    p.stdin.close(); p.wait()
    if poster is not None:
        poster.save(str(out_mp4).replace(".mp4", "_poster.png"))
    log(f"  reel rendered in {time.time()-t0:.1f}s")
    return total
