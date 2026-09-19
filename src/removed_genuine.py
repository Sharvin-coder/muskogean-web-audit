"""Quantify genuine Muskogean text lost to FineWeb-2 quality filters.

Applies the domain-level judgments in annotations_removed_domains.json to the
high-confidence removed sets; writes results/removed_genuine.json.
"""

import json
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
ann = json.loads((ROOT / "data/audit/annotations_removed_domains.json").read_text(
    encoding="utf-8"))

out = {}
for lang in ("cho", "mus"):
    rows = json.loads(
        (ROOT / f"data/audit/removed_hiprob_{lang}.json").read_text(encoding="utf-8"))
    a = ann[lang]
    verdicts = []
    for r in rows:
        dom = urlparse(r["url"]).netloc
        if dom in a["genuine"]:
            v = "genuine"
        elif dom in a["genuine_other_muskogean"]:
            v = "genuine_other_muskogean"
        elif dom in a["partial"]:
            v = "partial"
        else:
            v = "junk"
        verdicts.append({**r, "verdict": v, "domain": dom})

    gen = [r for r in verdicts if r["verdict"] == "genuine"]
    out[lang] = {
        "n_hiprob": len(rows),
        "verdicts": dict(Counter(r["verdict"] for r in verdicts)),
        "n_unique_urls_hiprob": len({r["url"] for r in rows}),
        "genuine_docs": len(gen),
        "genuine_unique_urls": len({r["url"] for r in gen}),
        "genuine_domains": sorted({r["domain"] for r in gen}),
        "genuine_by_filter_reason": dict(Counter(r["filter_reason"] for r in gen)),
        "kept_docs_for_reference": {"cho": 14, "mus": 10}[lang],
    }

(ROOT / "results/removed_genuine.json").write_text(json.dumps(out, indent=2))
print(json.dumps(out, indent=2))
