#!/usr/bin/env python3
"""Refuses to schedule anything unless (a) machine checks have zero failures and (b) a named reviewer approved every item.
Writes publish_queue.csv/json with a weekly cadence. Meta/Buffer/Later upload is the next adapter; the gate is the part that matters."""
import csv, datetime as dt, json, sys
from pathlib import Path
from engine import review

ROOT = Path(__file__).parent
SLOTS = [("09:00", 0), ("19:30", 0)]  # two posting slots per day, IST


def main():
    specs = [json.loads(p.read_text()) for p in sorted((ROOT / "specs").glob("*.json"))]
    log = json.loads((ROOT / "out" / "run_log.json").read_text())
    need = [i["id"] for i in review.items(specs)]
    fails = sum(r["fail"] for r in log["papers"].values())
    ap_path = ROOT / "approvals.json"
    ap = json.loads(ap_path.read_text()) if ap_path.exists() else {"reviewer": "", "approved": []}
    done = [i for i in need if i in set(ap["approved"])]
    print(f"machine checks: {fails} failures")
    print(f"doctor review : {len(done)}/{len(need)} items approved by '{ap.get('reviewer') or 'nobody'}'")
    if fails or len(done) != len(need) or not ap.get("reviewer"):
        print("BLOCKED: nothing scheduled. Open out/review.html, approve every item, paste approvals.json.")
        sys.exit(1)
    start = dt.date.today() + dt.timedelta(days=(7 - dt.date.today().weekday()) % 7 or 7)
    order = []
    for fmt in ("carousel", "reel", "static"):
        for sp in specs:
            order.append((sp["id"], fmt))
    rows, slots = [], []
    for d in range(7):
        for t, _ in SLOTS:
            slots.append((start + dt.timedelta(days=d), t))
    for (pid, fmt), (day, t) in zip(order, slots[1::1][: len(order)]):
        files = {"carousel": "carousel_*.png", "reel": "reel.mp4", "static": "static_4x5.png"}[fmt]
        rows.append({"when_ist": f"{day} {t}", "paper": pid, "format": fmt, "files": f"out/{pid}/{files}", "caption": f"out/{pid}/captions.txt", "approved_by": ap["reviewer"]})
    with open(ROOT / "out" / "publish_queue.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    print(f"APPROVED: {len(rows)} posts queued -> out/publish_queue.csv")


if __name__ == "__main__":
    main()
