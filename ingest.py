#!/usr/bin/env python3
"""paper in: local PDF/txt or URL -> papers/<name>.txt. Tested on .txt only in this build (PMC blocks scripted fetches from the sandbox)."""
import sys, urllib.request
from pathlib import Path

def ingest(src, name):
    out = Path(__file__).parent / "papers" / f"{name}.txt"
    if src.startswith("http"):
        raw = urllib.request.urlopen(urllib.request.Request(src, headers={"User-Agent": "steer-engine"})).read()
        if raw[:4] == b"%PDF":
            import io, pypdf
            text = "\n".join(p.extract_text() or "" for p in pypdf.PdfReader(io.BytesIO(raw)).pages)
        else:
            text = raw.decode("utf8", "ignore")
    elif src.lower().endswith(".pdf"):
        import pypdf
        text = "\n".join(p.extract_text() or "" for p in pypdf.PdfReader(src).pages)
    else:
        text = Path(src).read_text()
    out.write_text(f"SOURCE: {src}\n\n{text}")
    print("wrote", out)

if __name__ == "__main__":
    ingest(sys.argv[1], sys.argv[2])
