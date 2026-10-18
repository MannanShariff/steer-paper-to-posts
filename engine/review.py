"""Doctor review gate: one page per batch. Every claim is shown with its verbatim quote, source link, where it is used, and
machine check results. Steer-view statements (opinion, not study findings) are listed separately for sign-off."""
import html, json
from pathlib import Path
from .verify import slide_texts, strip_md


def items(specs):
    out = []
    for sp in specs:
        for c in sp["claims"]:
            out.append({"id": f"{sp['id']}:{c['id']}", "kind": "claim", "spec": sp["id"]})
        for i, sl in enumerate(sp["carousel"]["slides"], 1):
            if sl.get("steer_view"):
                out.append({"id": f"{sp['id']}:view:carousel{i}", "kind": "view", "spec": sp["id"]})
        for i, sc in enumerate(sp["reel"]["scenes"], 1):
            if sc.get("steer_view"):
                out.append({"id": f"{sp['id']}:view:reel{i}", "kind": "view", "spec": sp["id"]})
    return out


def _where(sp, cid):
    w = []
    for i, sl in enumerate(sp["carousel"]["slides"], 1):
        if cid in sl.get("claims", []): w.append(f"carousel {i}")
    if cid in sp["static"]["slide"].get("claims", []): w.append("static")
    for i, sc in enumerate(sp["reel"]["scenes"], 1):
        if cid in sc.get("claims", []): w.append(f"reel {i}")
    return ", ".join(w) or "unused"


CSS = """:root{--cream:#F5EBDF;--rust:#C04E2A;--ink:#351D1D;--clay:#8A5A4A;--blush:#E6CBBD;--paper:#F8F2EB}
*{box-sizing:border-box}body{margin:0;background:var(--cream);color:var(--ink);font:16px/1.55 Inter,system-ui,sans-serif;padding:24px 16px 80px}
main{max-width:980px;margin:0 auto}h1,h2,h3{font-family:Lora,Georgia,serif;font-weight:500;margin:0}h1{font-size:40px}h1 em,h2 em{color:var(--rust)}
h2{font-size:30px;margin-top:48px}.mark{font-family:Lora,Georgia,serif;color:var(--rust);font-size:28px;font-weight:600}
.sub{color:var(--clay)}.card{background:var(--paper);border:1px solid var(--blush);border-radius:14px;padding:16px 18px;margin:12px 0}
.strip{display:flex;gap:8px;overflow-x:auto;padding:6px 0}.strip img{height:230px;border:1px solid var(--blush);border-radius:8px}
table{width:100%;border-collapse:collapse}td,th{padding:10px 8px;border-top:1px solid var(--blush);vertical-align:top;text-align:left}th{font-size:12px;color:var(--clay);font-weight:600;letter-spacing:.06em}
blockquote{margin:0;font-family:Lora,Georgia,serif;font-style:italic}.pill{display:inline-block;padding:2px 10px;border-radius:99px;font-size:12px;font-weight:700}
.ok{background:#e4dccf;color:var(--ink)}.bad{background:var(--rust);color:#fff}a{color:var(--rust)}
input[type=text]{font:inherit;padding:10px 12px;border:1.5px solid var(--blush);border-radius:10px;background:#fffaf4;width:100%;max-width:340px}
button{font:inherit;font-weight:700;padding:12px 20px;border-radius:99px;border:1.5px solid var(--rust);background:var(--rust);color:#fff8f0;cursor:pointer}
input[type=checkbox]{width:20px;height:20px;accent-color:var(--rust)}.bar{position:sticky;bottom:0;background:var(--cream);border-top:1px solid var(--blush);padding:12px 0;margin-top:30px;display:flex;gap:14px;align-items:center;flex-wrap:wrap}
pre{white-space:pre-wrap;background:var(--paper);border:1px solid var(--blush);border-radius:10px;padding:12px;font-size:13px}"""


def build_review(specs, reports, out_path, rel="."):
    its = items(specs)
    h = [f"<!doctype html><meta charset=utf-8><meta name=viewport content='width=device-width,initial-scale=1'><title>Steer review gate</title><style>{CSS}</style><main>",
         "<div class=mark>steer</div><h1>Review gate: <em>approve before anything posts</em></h1>",
         "<p class=sub>Each claim below is linked to its verbatim source quote. Tick a claim only after checking it against the full paper. Nothing is scheduled until every item is approved.</p>"]
    for sp in specs:
        rep = reports[sp["id"]]
        fails = [r for r in rep["verify"] + rep["lint"] if r[0] == "FAIL"]
        notes = [r for r in rep["verify"] if r[0] == "NOTE"]
        h.append(f"<h2>{html.escape(sp['paper']['title'])}</h2>")
        h.append(f"<p class=sub>Source: <a href='{sp['paper']['url']}'>{html.escape(sp['paper']['short'])}</a> &middot; machine checks: "
                 f"<span class='pill {'bad' if fails else 'ok'}'>{len(fails)} failures</span> <span class='pill ok'>{len(notes)} notes</span></p>")
        h.append(f"<div class=card><b>Message.</b> {html.escape(sp['message'])}<br><b>Why it works.</b> {html.escape(sp['reasoning'])}</div>")
        imgs = "".join(f"<img loading=lazy src='{rel}/{sp['id']}/{f.name}'>" for f in sorted((Path(out_path).parent / sp["id"]).glob("carousel_*.png")))
        imgs += f"<img loading=lazy src='{rel}/{sp['id']}/static_4x5.png'>"
        h.append(f"<div class=strip>{imgs}</div>")
        h.append("<table><tr><th>OK</th><th>CLAIM</th><th>VERBATIM QUOTE FROM SOURCE</th><th>USED IN</th></tr>")
        for c in sp["claims"]:
            iid = f"{sp['id']}:{c['id']}"
            h.append(f"<tr><td><input type=checkbox data-id='{iid}'></td><td><b>{c['id']}</b></td><td><blockquote>&ldquo;{html.escape(c['quote'])}&rdquo;</blockquote></td><td>{_where(sp, c['id'])}</td></tr>")
        h.append("</table>")
        views = []
        for i, sl in enumerate(sp["carousel"]["slides"], 1):
            if sl.get("steer_view"): views.append((f"{sp['id']}:view:carousel{i}", f"carousel {i}", " / ".join(strip_md(t) for t in slide_texts(sl))))
        for i, sc in enumerate(sp["reel"]["scenes"], 1):
            if sc.get("steer_view"): views.append((f"{sp['id']}:view:reel{i}", f"reel {i}", sc["say"]))
        if views:
            h.append("<h3 style='margin-top:20px'>Steer view statements (opinion, not study findings)</h3><table>")
            for iid, wh, tx in views:
                h.append(f"<tr><td><input type=checkbox data-id='{iid}'></td><td>{wh}</td><td>{html.escape(tx)}</td></tr>")
            h.append("</table>")
        for r in fails:
            h.append(f"<p><span class='pill bad'>FAIL</span> {html.escape(r[1])}: {html.escape(r[2])}</p>")
    h.append("<div class=bar><label>Reviewer name <input type=text id=rv placeholder='Dr ...'></label><button id=cp>Copy approvals JSON</button><span id=msg class=sub></span></div>")
    h.append("<p class=sub>Paste the copied JSON into approvals.json, then run <code>python publish_gate.py</code>.</p><pre id=out></pre>")
    allids = json.dumps([i["id"] for i in its])
    h.append(f"""<script>const ALL={allids};
document.getElementById('cp').onclick=function(){{const ok=[...document.querySelectorAll('input[data-id]:checked')].map(e=>e.dataset.id);
const j=JSON.stringify({{reviewer:document.getElementById('rv').value.trim(),approved:ok,total:ALL.length}},null,2);
document.getElementById('out').textContent=j;const m=document.getElementById('msg');
(navigator.clipboard?navigator.clipboard.writeText(j):Promise.reject()).then(()=>m.textContent=ok.length+' of '+ALL.length+' approved. Copied.',()=>m.textContent=ok.length+' of '+ALL.length+' approved. Select the text below and copy.');}}</script></main>""")
    Path(out_path).write_text("\n".join(h))
