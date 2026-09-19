"""Aggregate the manual precision-audit annotations over the kept documents.

Reads data/audit/annotations_kept.json + data/audit/kept_docs_full.json,
writes results/audit_kept.json.
"""

import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

docs = {d["doc_id"]: d for d in json.loads(
    (ROOT / "data/audit/kept_docs_full.json").read_text(encoding="utf-8"))}
ann = json.loads(
    (ROOT / "data/audit/annotations_kept.json").read_text(encoding="utf-8"))["docs"]
assert len(ann) == len(docs) == 28

CONTEMP = ("contemporary", "contemporary reference")
RELIGIOUS = ("bible", "religious-org", "wiki-canonical")


def subset(a):
    return "glotcc_cho" if a["doc_id"].startswith("glotcc") else (
        "fw2_cho" if "_cho" in a["doc_id"] else "fw2_mus")


out = {"n_docs": len(ann), "per_subset": {}}
for sub in ("fw2_cho", "fw2_mus", "glotcc_cho"):
    rows = [a for a in ann if subset(a) == sub]
    chars = {a["doc_id"]: len(docs[a["doc_id"]]["text"]) for a in rows}
    total = sum(chars.values())
    clusters = Counter(a["content_cluster"] for a in rows)
    out["per_subset"][sub] = {
        "n_docs": len(rows),
        "total_chars": total,
        "is_target": dict(Counter(a["is_target_language"] for a in rows)),
        "genre": dict(Counter(a["genre"] for a in rows)),
        "n_content_clusters": len(clusters),
        "duplicated_docs": sum(v for v in clusters.values() if v > 1),
        "religious_char_frac": round(sum(
            chars[a["doc_id"]] for a in rows if a["genre"] in RELIGIOUS) / total, 3),
        "contemporary_char_frac": round(sum(
            chars[a["doc_id"]] for a in rows
            if a["source_era"] in CONTEMP) / total, 3),
        "mean_boilerplate_frac": round(
            sum(a["boilerplate_frac"] for a in rows) / len(rows), 3),
    }

all_clusters = Counter(a["content_cluster"] for a in ann)
out["overall"] = {
    "n_content_clusters": len(all_clusters),
    "docs_in_multi_doc_clusters": sum(v for v in all_clusters.values() if v > 1),
    "is_target": dict(Counter(a["is_target_language"] for a in ann)),
    "genre_chars": {
        g: sum(len(docs[a["doc_id"]]["text"]) for a in ann if a["genre"] == g)
        for g in sorted({a["genre"] for a in ann})
    },
    "test_split_contamination": "cho_Latn test split = 1 doc (fw2_cho_test_0), "
    "near-duplicate of train docs fw2_cho_11, fw2_cho_12 (UDHR Art. 1)",
}

(ROOT / "results/audit_kept.json").write_text(json.dumps(out, indent=2))
print(json.dumps(out, indent=2))
