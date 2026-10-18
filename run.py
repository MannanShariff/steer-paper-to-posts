#!/usr/bin/env python3
"""paper -> posts. Usage: python run.py [spec ids...]
Stages: verify -> lint -> render carousel/static/reel -> captions -> review page. Timings go to out/run_log.json."""
import json, sys, time
from pathlib import Path
from engine import verify, lint, render as R, reel, review

ROOT = Path(__file__).parent
OUT = ROOT / "out"


def alt(sl):
    from engine.verify import slide_texts, strip_md
    return ". ".join(strip_md(t) for t in slide_texts(sl))


def run_one(spec, log):
    pid, tag = spec["id"], spec["paper"]["tag"]
    d = OUT / pid; d.mkdir(parents=True, exist_ok=True)
    stages, t0 = {}, time.time()
    def stage(name, fn):
        s = time.time(); r = fn(); stages[name] = round(time.time() - s, 1); return r
    v = stage("verify", lambda: verify.verify_spec(spec, ROOT))
    l = stage("lint", lambda: lint.lint_spec(spec))
    n = len(spec["carousel"]["slides"])
    def carousel():
        for i, sl in enumerate(spec["carousel"]["slides"], 1):
            R.draw(R.build(sl, "feed", tag, i, n)).save(d / f"carousel_{i:02d}.png")
    stage("carousel", carousel)
    def static():
        sl = spec["static"]["slide"]
        for mode, name in (("feed", "4x5"), ("square", "1x1"), ("story", "9x16")):
            R.draw(R.build(sl, mode, tag, 1, 1)).save(d / f"static_{name}.png")
    stage("static+resizes", static)
    stage("reel", lambda: reel.render_reel(spec, d / "reel.mp4", tag, d / "_work", log=lambda *_: None))
    import shutil; shutil.rmtree(d / "_work", ignore_errors=True)
    def captions():
        parts = []
        for k, title in (("carousel", "CAROUSEL"), ("static", "STATIC"), ("reel", "REEL")):
            parts.append(f"=== {title} ===\n{spec[k]['caption']}\n\n{' '.join(spec[k].get('hashtags', []))}\n")
        parts.append("=== ALT TEXT (carousel) ===\n" + "\n".join(f"{i}. {alt(s)}" for i, s in enumerate(spec["carousel"]["slides"], 1)))
        (d / "captions.txt").write_text("\n".join(parts))
        (d / "captions_hinglish.txt").write_text(spec["carousel"].get("caption_hi", "") + "\n\n" + " ".join(spec["carousel"].get("hashtags", [])))
        (d / "claims.json").write_text(json.dumps({"paper": spec["paper"], "claims": spec["claims"], "message": spec["message"], "reasoning": spec["reasoning"]}, indent=2))
    stage("captions", captions)
    stages["total"] = round(time.time() - t0, 1)
    fails = [r for r in v + l if r[0] == "FAIL"]
    log["papers"][pid] = {"stages_sec": stages, "fail": len(fails), "notes": len([r for r in v if r[0] == "NOTE"]),
                          "failures": [list(r) for r in fails]}
    print(f"{pid}: {stages['total']}s machine time, {len(fails)} failures, {log['papers'][pid]['notes']} notes")
    return {"verify": v, "lint": l}


def main():
    ids = sys.argv[1:]
    specs = [json.loads(p.read_text()) for p in sorted((ROOT / "specs").glob("*.json"))]
    if ids:
        specs = [s for s in specs if s["id"] in ids]
    OUT.mkdir(exist_ok=True)
    log = {"papers": {}}
    t0 = time.time()
    reports = {s["id"]: run_one(s, log) for s in specs}
    review.build_review(specs, reports, OUT / "review.html")
    log["batch_sec"] = round(time.time() - t0, 1)
    (OUT / "run_log.json").write_text(json.dumps(log, indent=2))
    print(f"batch of {len(specs)} papers: {log['batch_sec']}s machine time. Review page: out/review.html")


if __name__ == "__main__":
    main()
