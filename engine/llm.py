"""Optional unattended step: paper text -> claims -> spec using the Anthropic API.
NOT exercised in the hackathon build: this sandbox has no API key and blocks outbound calls, so the three specs in specs/ were
written by Claude in-session following prompts/extract.md and prompts/translate.md. Everything after this step is tested."""
import json, os, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MODEL = os.environ.get("STEER_MODEL", "claude-sonnet-5-5")


def _call(system, user):
    req = urllib.request.Request("https://api.anthropic.com/v1/messages", method="POST",
        headers={"x-api-key": os.environ["ANTHROPIC_API_KEY"], "anthropic-version": "2023-06-01", "content-type": "application/json"},
        data=json.dumps({"model": MODEL, "max_tokens": 8000, "system": system, "messages": [{"role": "user", "content": user}]}).encode())
    return json.load(urllib.request.urlopen(req))["content"][0]["text"]


def paper_to_spec(paper_file, spec_id):
    text = Path(paper_file).read_text()
    claims = json.loads(_call((ROOT / "prompts/extract.md").read_text(), text))
    spec = json.loads(_call((ROOT / "prompts/translate.md").read_text(), json.dumps({"claims": claims, "example": json.loads((ROOT / "specs/regain.json").read_text())})))
    spec["id"], spec["claims"] = spec_id, claims["claims"]
    (ROOT / "specs" / f"{spec_id}.json").write_text(json.dumps(spec, indent=2))
    return spec
