"""T5 (camera-ready): second-LID cross-check requested by reviewers.

No public LID system other than GlotLID carries any Muskogean label
(fastText lid.176: 176 labels; OpenLID: 201; NLLB-LID: 218). We therefore
run fastText lid.176 as the second system and characterize where
(a) the high-confidence removed documents (both junk and genuine, per our
domain-level verdicts) and (b) the 14 verified seed segments land when no
Muskogean label exists.

Writes results/lid_crosscheck.json.
"""

import io
import json
import os
import subprocess
import time
from collections import Counter
from pathlib import Path
from urllib.parse import urlsplit

import fasttext

ROOT = Path(__file__).resolve().parents[1]
MODEL = os.environ.get("LID176_MODEL", "models/lid.176.ftz")

model = fasttext.load_model(MODEL)
_all, _ = model.predict("a", k=1000)
N_LABELS = len(set(_all))
MUSKOGEAN = {"cho", "cic", "mus", "akz", "cku", "mik"}
has_muskogean = any(l.replace("__label__", "") in MUSKOGEAN for l in _all)


def top1(text):
    labels, probs = model.predict(text.replace("\n", " ")[:4000], k=1)
    return labels[0].replace("__label__", ""), round(float(probs[0]), 3)


t0 = time.time()

# -- (a) high-confidence removed docs, with our domain-level verdicts -------
ann = json.loads((ROOT / "data/audit/annotations_removed_domains.json"
                  ).read_text(encoding="utf-8"))
removed = {}
for lang in ("cho", "mus"):
    genuine_domains = set(ann[lang].get("genuine", []) +
                          ann[lang].get("genuine-other-muskogean", []))
    docs = json.loads((ROOT / f"data/audit/removed_hiprob_{lang}.json"
                       ).read_text(encoding="utf-8"))
    rows = []
    for d in docs:
        dom = urlsplit(d["url"]).netloc.lower()
        verdict = "genuine" if dom in genuine_domains else "junk_or_partial"
        lab, p = top1(d["text"])
        rows.append({"verdict": verdict, "ft_label": lab, "ft_prob": p,
                     "n_chars": len(d["text"])})
    junk = [r for r in rows if r["verdict"] != "genuine"]
    gen = [r for r in rows if r["verdict"] == "genuine"]

    def agg(rs):
        if not rs:
            return {}
        return {
            "n": len(rs),
            "top_labels": Counter(r["ft_label"] for r in rs).most_common(8),
            "mean_prob": round(sum(r["ft_prob"] for r in rs) / len(rs), 3),
            "frac_below_p50": round(
                sum(1 for r in rs if r["ft_prob"] < 0.5) / len(rs), 3),
        }
    removed[lang] = {"junk_or_partial": agg(junk), "genuine": agg(gen),
                     "rows": rows}

# -- (b) verified seed segments ---------------------------------------------
segs = json.loads((ROOT / "data/seed/seed_segments.json"
                   ).read_text(encoding="utf-8"))
seed_out = []
for s in segs:
    lab, p = top1(s["text"])
    seed_out.append({"lang": s["lang"], "name": s["name"],
                     "n_chars": s["n_chars"], "ft_label": lab, "ft_prob": p})

res = {
    "config": {
        "script": "src/lid_crosscheck.py",
        "model": "fastText lid.176.ftz (quantized), 176 labels",
        "model_labels": N_LABELS,
        "contains_any_muskogean_label": has_muskogean,
        "git_hash": subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"], cwd=ROOT,
            capture_output=True, text=True).stdout.strip(),
        "run_unix": int(time.time()),
    },
    "runtime_s": round(time.time() - t0, 1),
    "removed_hiprob": {k: {kk: vv for kk, vv in v.items() if kk != "rows"}
                       for k, v in removed.items()},
    "removed_rows": {k: v["rows"] for k, v in removed.items()},
    "seed_segments": seed_out,
}
io.open(ROOT / "results/lid_crosscheck.json", "w", encoding="utf-8").write(
    json.dumps(res, indent=1, ensure_ascii=False))

print("muskogean label present:", has_muskogean, "| labels:", N_LABELS)
for lang in ("cho", "mus"):
    for grp in ("junk_or_partial", "genuine"):
        print(lang, grp, json.dumps(removed[lang][grp] and
              {k: removed[lang][grp][k] for k in
               ("n", "top_labels", "mean_prob", "frac_below_p50")}))
print("--- seed segments ---")
for s in seed_out:
    print(f"{s['lang']:4} {s['name']:22} -> {s['ft_label']:4} {s['ft_prob']}")
print(f"{res['runtime_s']}s")
