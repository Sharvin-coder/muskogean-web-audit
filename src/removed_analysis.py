"""Analyze the FineWeb-2 removed piles for cho_Latn and mus_Latn.

For every removed document: filter_reason, domain, and a GlotLID v3
re-identification of its text. Writes results/removed_analysis.json and a
stratified sample to data/audit/removed_sample.json for manual checking.
"""

import json
import random
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse

import os

import fasttext
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
MODEL = os.environ.get("GLOTLID_MODEL", "models/glotlid_v3_model.bin")

random.seed(0)
model = fasttext.load_model(MODEL)


def relabel(texts):
    labels, probs = [], []
    for t in texts:
        l, p = model.predict(" ".join(t.split())[:2000], k=1)
        labels.append(l[0].removeprefix("__label__"))
        probs.append(float(p[0]))
    return labels, probs


out = {}
samples = {}
for lang in ("cho", "mus"):
    df = pd.read_parquet(
        ROOT / f"data/raw/HuggingFaceFW__fineweb-2/data/{lang}_Latn_removed/train/000_00000.parquet"
    )
    df["domain"] = df.url.map(lambda u: urlparse(u).netloc)
    labels, probs = relabel(df.text.tolist())
    df["glotlid_v3"] = labels
    df["glotlid_v3_prob"] = probs
    still = df.glotlid_v3 == f"{lang}_Latn"

    out[f"{lang}_Latn_removed"] = {
        "n_docs": len(df),
        "filter_reason": df.filter_reason.value_counts().to_dict(),
        "median_chars": int(df.text.str.len().median()),
        "n_domains": int(df.domain.nunique()),
        "top_domains": df.domain.value_counts().head(12).to_dict(),
        "glotlid_v3_top15": df.glotlid_v3.value_counts().head(15).to_dict(),
        "still_target_n": int(still.sum()),
        "still_target_frac": round(float(still.mean()), 4),
        "still_target_domains": df[still].domain.value_counts().head(12).to_dict(),
        "top_domain_relabel": {
            dom: df[df.domain == dom].glotlid_v3.value_counts().head(3).to_dict()
            for dom in df.domain.value_counts().head(5).index
        },
    }

    # persist per-doc relabels + the high-confidence subset for manual annotation
    df[["url", "filter_reason", "glotlid_v3", "glotlid_v3_prob"]].to_csv(
        ROOT / f"results/removed_relabel_{lang}.csv.gz", index=False)
    hi = df[(df.glotlid_v3 == f"{lang}_Latn") & (df.glotlid_v3_prob >= 0.9)]
    hi_rows = [
        {"idx": int(i), "url": r.url, "filter_reason": r.filter_reason,
         "prob": round(float(r.glotlid_v3_prob), 3), "text": r.text[:800]}
        for i, r in hi.iterrows()
    ]
    (ROOT / f"data/audit/removed_hiprob_{lang}.json").write_text(
        json.dumps(hi_rows, indent=1, ensure_ascii=False), encoding="utf-8")
    out[f"{lang}_Latn_removed"]["n_hiprob_target"] = len(hi_rows)

    # stratified sample for manual check: up to 3 docs per (filter_reason)
    # plus all docs still identified as the target language (capped at 40)
    sample_rows = []
    for reason, grp in df.groupby("filter_reason"):
        idx = random.sample(list(grp.index), min(3, len(grp)))
        sample_rows += [
            {"stratum": f"reason:{reason}", "url": df.url[i],
             "glotlid_v3": df.glotlid_v3[i], "prob": round(float(df.glotlid_v3_prob[i]), 3),
             "text": df.text[i][:600]}
            for i in idx
        ]
    still_idx = list(df[still].index)
    for i in (random.sample(still_idx, 40) if len(still_idx) > 40 else still_idx):
        sample_rows.append(
            {"stratum": "still_target", "url": df.url[i],
             "glotlid_v3": df.glotlid_v3[i], "prob": round(float(df.glotlid_v3_prob[i]), 3),
             "filter_reason": df.filter_reason[i], "text": df.text[i][:600]}
        )
    samples[lang] = sample_rows

(ROOT / "results/removed_analysis.json").write_text(json.dumps(out, indent=2))
(ROOT / "data/audit/removed_sample.json").write_text(
    json.dumps(samples, indent=1, ensure_ascii=False), encoding="utf-8")
print(json.dumps({k: {kk: vv for kk, vv in v.items()
                      if kk in ("n_docs", "still_target_n", "still_target_frac",
                                "glotlid_v3_top15", "still_target_domains")}
                  for k, v in out.items()}, indent=2))
