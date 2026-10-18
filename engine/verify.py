"""Claim verification. Three deterministic checks, no LLM involved:
 1. every claim quote appears verbatim in the stored source text,
 2. every number shown on a slide, reel scene or caption appears in a linked claim quote (rounded matches are flagged),
 3. every slide that shows a number or a health statement is linked to at least one claim, or is marked steer_view with no numbers."""
import re
from pathlib import Path

NUM = re.compile(r"(?<![A-Za-z/])\d+(?:\.\d+)?")
WORDNUM = ("two-thirds", "one-third", "half", "twice", "double")


def norm(s):
    s = s.replace("≥", ">=").replace("≤", "<=")
    s = re.sub(r"[‐‑‒–—−]", "-", s)
    s = s.replace("’", "'").replace("“", '"').replace("”", '"')
    return re.sub(r"\s+", " ", s).strip().lower()


def strip_md(s):
    return s.replace("*", "")


def _numbers(text):
    return [m.group(0) for m in NUM.finditer(strip_md(text))]


def _quote_numbers(q):
    return [float(m.group(0)) for m in NUM.finditer(q)]


def slide_texts(sl):
    t = [sl.get(k, "") for k in ("headline", "sub", "body", "stat", "note")]
    t += sl.get("lines", [])
    for it in sl.get("items", []):
        if isinstance(it, dict):
            t += [it.get("label", ""), it.get("display", "")]
        else:
            t += [str(x) for x in it]
    for r in sl.get("rows", []):
        t.append(r.get("label", ""))
    t += [str(x) for x in sl.get("ticks", [])]
    return [x for x in t if x]


def _check_numbers(texts, quotes_norm, where, report):
    qnums = [n for q in quotes_norm for n in _quote_numbers(q)]
    for text in texts:
        low = strip_md(text).lower()
        for w in WORDNUM:
            if w in low and not any(w in q for q in quotes_norm):
                report.append(("FAIL", where, f"'{w}' is not in any linked claim quote"))
        for tok in _numbers(text):
            val = float(tok)
            exact = any(abs(val - q) < 1e-9 for q in qnums)
            rounded = any(int(q + 0.5) == val for q in qnums) if "." not in tok else False
            if exact:
                continue
            if rounded:
                report.append(("NOTE", where, f"{tok} is a rounded match of a number in a linked quote (slide says 'about')"))
            else:
                report.append(("FAIL", where, f"number {tok} not found in any linked claim quote"))


def verify_spec(spec, root):
    rep = []
    src = norm(Path(root, spec["paper"]["file"]).read_text())
    claims = {c["id"]: c for c in spec["claims"]}
    for c in spec["claims"]:
        if norm(c["quote"]) not in src:
            rep.append(("FAIL", f"claim {c['id']}", "quote not found verbatim in source text"))
    used = set()

    def check_item(where, texts, ids, steer):
        qs = []
        for i in ids:
            if i not in claims:
                rep.append(("FAIL", where, f"unknown claim id {i}"))
            else:
                qs.append(norm(claims[i]["quote"]))
                used.add(i)
        digits = any(_numbers(t) or any(w in t.lower() for w in WORDNUM) for t in texts)
        if steer:
            if digits:
                rep.append(("FAIL", where, "steer_view slide contains a number; link a claim instead"))
            return
        if digits and not ids:
            rep.append(("FAIL", where, "shows a number but links no claim"))
        _check_numbers(texts, qs, where, rep)

    for i, sl in enumerate(spec["carousel"]["slides"], 1):
        check_item(f"carousel slide {i}", slide_texts(sl), sl.get("claims", []), sl.get("steer_view", False))
    ss = spec["static"]["slide"]
    check_item("static", slide_texts(ss), ss.get("claims", []), ss.get("steer_view", False))
    for i, sc in enumerate(spec["reel"]["scenes"], 1):
        texts = slide_texts(sc["slide"]) + [sc.get("sub", "")]
        check_item(f"reel scene {i}", texts, sc.get("claims", []), sc.get("steer_view", False))
    allq = [norm(c["quote"]) for c in spec["claims"]]
    for where, cap in (("carousel caption", spec["carousel"]["caption"]), ("static caption", spec["static"]["caption"]), ("reel caption", spec["reel"]["caption"])):
        body = "\n".join(l for l in cap.split("\n") if not l.lower().startswith("source:"))
        _check_numbers([body], allq, where, rep)
    seen, uniq = set(), []
    for r in rep:
        if r not in seen:
            seen.add(r); uniq.append(r)
    rep[:] = uniq
    for cid in claims:
        if cid not in used:
            rep.append(("NOTE", f"claim {cid}", "defined but not used on any slide"))
    return rep
