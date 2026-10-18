"""Negative tests: the gates must reject fabricated or non-compliant content."""
import copy, json, sys, unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from engine import verify, lint

BASE = json.loads((ROOT / "specs/regain.json").read_text())


def fails(rep):
    return [r for r in rep if r[0] == "FAIL"]


class Gates(unittest.TestCase):
    def test_shipped_specs_clean(self):
        for p in (ROOT / "specs").glob("*.json"):
            s = json.loads(p.read_text())
            self.assertEqual(fails(verify.verify_spec(s, ROOT)), [], p.name)
            self.assertEqual(lint.lint_spec(s), [], p.name)

    def test_fabricated_number_is_caught(self):
        s = copy.deepcopy(BASE)
        s["carousel"]["slides"][1]["headline"] = "of the weight lost, 85% had come back."
        self.assertTrue(any("85" in r[2] for r in fails(verify.verify_spec(s, ROOT))))

    def test_invented_quote_is_caught(self):
        s = copy.deepcopy(BASE)
        s["claims"][0]["quote"] = "participants regained all of their prior weight loss"
        self.assertTrue(any("not found verbatim" in r[2] for r in fails(verify.verify_spec(s, ROOT))))

    def test_number_without_claim_is_caught(self):
        s = copy.deepcopy(BASE)
        s["carousel"]["slides"][5]["lines"][0] = "Most people regain 70% of it."
        self.assertTrue(fails(verify.verify_spec(s, ROOT)))

    def test_drug_name_promise_shame_caps(self):
        for text in ("Semaglutide works", "Lose 10 kg fast", "A miracle for lazy people", "STOP eating"):
            self.assertTrue(lint.lint_text(text, "t"), text)

    def test_wrong_word_number(self):
        s = copy.deepcopy(BASE)
        s["carousel"]["slides"][1]["stat"] = "half"
        self.assertTrue(fails(verify.verify_spec(s, ROOT)))


if __name__ == "__main__":
    unittest.main()
