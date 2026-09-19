"""Recall-side LID stress test on the verified Muskogean seed set.

Conditions per segment:
  full        — text as extracted
  no_diacrit  — combining marks removed, special letters ASCII-folded
  chunks8     — 8-word chunks (web-fragment condition); majority label reported

Writes results/lid_stress.json.
"""

import json
import unicodedata
from collections import Counter
from pathlib import Path

import os

import fasttext

ROOT = Path(__file__).resolve().parents[1]
model = fasttext.load_model(
    os.environ.get("GLOTLID_MODEL", "models/glotlid_v3_model.bin"))

FOLD = str.maketrans({"ʊ": "u", "Ʊ": "U", "ʋ": "v", "Ʋ": "V", "ł": "l",
                      "Ł": "L", "ə": "e", "ʔ": "'", "ɬ": "lh"})


def strip_diacritics(s: str) -> str:
    s = unicodedata.normalize("NFD", s.translate(FOLD))
    return "".join(c for c in s if unicodedata.category(c) != "Mn")


def pred(text: str, k: int = 3):
    labels, probs = model.predict(" ".join(text.split()), k=k)
    return [(l.removeprefix("__label__"), round(float(p), 3))
            for l, p in zip(labels, probs)]


segments = json.loads(
    (ROOT / "data/seed/seed_segments.json").read_text(encoding="utf-8"))
HAS_LABEL = {"cho": "cho_Latn", "mus": "mus_Latn"}

results = []
for s in segments:
    text = s["text"]
    row = {k: s[k] for k in ("lang", "name", "type", "url", "n_chars")}
    row["expected"] = HAS_LABEL.get(s["lang"], "NO_LABEL_EXISTS")

    row["full"] = pred(text)
    row["no_diacrit"] = pred(strip_diacritics(text))

    words = text.split()
    chunks = [" ".join(words[i:i + 8]) for i in range(0, len(words), 8)]
    chunk_preds = [pred(c, k=1)[0][0] for c in chunks if c.strip()]
    row["chunks8"] = {
        "n_chunks": len(chunk_preds),
        "label_dist": dict(Counter(chunk_preds).most_common(5)),
    }

    for cond in ("full", "no_diacrit"):
        row[f"{cond}_correct"] = (
            row[cond][0][0] == row["expected"] if s["lang"] in HAS_LABEL else None)
    if s["lang"] in HAS_LABEL:
        row["chunks8_recall"] = round(
            sum(1 for p in chunk_preds if p == HAS_LABEL[s["lang"]])
            / max(len(chunk_preds), 1), 3)
    results.append(row)

summary = {
    "per_segment": results,
    "labeled_langs_full_acc": {
        lang: [r["full_correct"] for r in results if r["lang"] == lang]
        for lang in ("cho", "mus")
    },
    "unlabeled_lang_assignments": {
        r["lang"] + "/" + r["name"]: r["full"][0]
        for r in results if r["expected"] == "NO_LABEL_EXISTS"
    },
}
(ROOT / "results/lid_stress.json").write_text(json.dumps(summary, indent=2))
print(json.dumps(summary, indent=2))
