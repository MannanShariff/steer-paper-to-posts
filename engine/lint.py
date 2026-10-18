"""Steer voice + compliance linter. Runs on every public string (slides, narration, subtitles, captions, hashtags)."""
import re

DRUGS = r"semaglutide|tirzepatide|ozempic|wegovy|mounjaro|zepbound|rybelsus|saxenda|liraglutide|retatrutide|novo nordisk|eli lilly"
RULES = [
    ("drug or brand name", re.compile(rf"\b({DRUGS})\b", re.I)),
    ("hype or miracle language", re.compile(r"\b(miracle|magic|guarantee[d]?|melt(s|ing)?|shred(s|ded)?|burn fat|quick fix|effortless|overnight|secret|game.?changer|breakthrough)\b", re.I)),
    ("weight-loss promise", re.compile(r"\b(lose|drop|shed)\s+(up to\s+)?\d+\s*(kg|kgs|kilos?|pounds?|lbs?|%|percent)", re.I)),
    ("before/after body language", re.compile(r"before\s*(and|/|&)\s*after|transformation", re.I)),
    ("fear, shame or blame language", re.compile(r"\b(lazy|ashamed|shame|disgust\w*|embarrass\w*|fat shaming|hopeless|failure to)\b", re.I)),
    ("pressure language", re.compile(r"\b(act now|limited time|hurry|don't miss|last chance)\b", re.I)),
    ("emoji or hype punctuation", re.compile("[\U0001F300-\U0001FAFF☀-➿]|!!")),
]
ALLOW_CAPS = {"DEXA", "BMI", "GLP", "WHO", "WC", "IST", "STEP", "ENDO"}


def lint_text(text, where):
    out = []
    for name, rx in RULES:
        m = rx.search(text)
        if m:
            out.append(("FAIL", where, f"{name}: '{m.group(0)}'"))
    for w in re.findall(r"\b[A-Z]{4,}\b", text):
        if w not in ALLOW_CAPS:
            out.append(("FAIL", where, f"ALL CAPS word '{w}' (brand voice is sentence case)"))
    return out


def lint_spec(spec):
    rep = []
    def go(where, text):
        rep.extend(lint_text(text.replace("*", ""), where))
    from .verify import slide_texts
    for i, sl in enumerate(spec["carousel"]["slides"], 1):
        for t in slide_texts(sl) + [sl.get("pill", ""), sl.get("small", "")]:
            go(f"carousel slide {i}", t)
    for t in slide_texts(spec["static"]["slide"]):
        go("static", t)
    for i, sc in enumerate(spec["reel"]["scenes"], 1):
        for t in slide_texts(sc["slide"]) + [sc.get("say", ""), sc.get("sub", "")]:
            go(f"reel scene {i}", t)
    for where, key in (("carousel caption", spec["carousel"]), ("static caption", spec["static"]), ("reel caption", spec["reel"])):
        go(where, key["caption"])
        go(where + " hashtags", " ".join(key.get("hashtags", [])))
    if "caption_hi" in spec["carousel"]:
        go("carousel caption (Hinglish)", spec["carousel"]["caption_hi"])
    if "steerclub.com" not in spec["carousel"]["caption"] + spec["static"]["caption"] + spec["reel"]["caption"]:
        rep.append(("FAIL", "captions", "missing steerclub.com sign-off"))
    for where, cap in (("carousel caption", spec["carousel"]["caption"]), ("static caption", spec["static"]["caption"]), ("reel caption", spec["reel"]["caption"])):
        if "source:" not in cap.lower():
            rep.append(("FAIL", where, "no Source line"))
    return rep
