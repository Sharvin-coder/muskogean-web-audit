"""First-pass inventory of every Muskogean-labeled document we downloaded.

Prints per-subset counts, domains, and length stats; exports each subset to
data/audit/<subset>.jsonl for the manual audit pass.
"""

import json
from pathlib import Path
from urllib.parse import urlparse

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
AUDIT = ROOT / "data" / "audit"
AUDIT.mkdir(parents=True, exist_ok=True)

manifest = json.loads((RAW / "manifest.json").read_text())

# group parquet files into subsets like fineweb-2/cho_Latn, glotcc/cho-Latn
subsets: dict[str, list[str]] = {}
for entry in manifest:
    parts = Path(entry["path"]).parts
    name = ("fineweb-2/" + parts[1]) if "fineweb-2" in entry["repo"] else (
        "glotcc/" + parts[1]
    )
    subsets.setdefault(name, []).append(entry["local"])

summary = []
for name, files in sorted(subsets.items()):
    df = pd.concat([pd.read_parquet(f) for f in files], ignore_index=True)
    url_col = next(
        (c for c in df.columns if "url" in c.lower() or "uri" in c.lower()), None
    )
    text_col = "text" if "text" in df.columns else "content"
    domains = (
        df[url_col].map(lambda u: urlparse(u).netloc).value_counts()
        if url_col
        else pd.Series(dtype=int)
    )
    chars = df[text_col].str.len()
    row = {
        "subset": name,
        "docs": len(df),
        "total_chars": int(chars.sum()),
        "median_chars": int(chars.median()),
        "unique_domains": int(domains.size),
        "top_domains": domains.head(10).to_dict(),
        "columns": list(df.columns),
    }
    summary.append(row)

    out = AUDIT / (name.replace("/", "_") + ".jsonl")
    keep = [c for c in (text_col, url_col, "date", "id") if c and c in df.columns]
    df[keep].to_json(out, orient="records", lines=True, force_ascii=False)

print(json.dumps(summary, indent=2))
(ROOT / "results").mkdir(exist_ok=True)
(ROOT / "results" / "inventory.json").write_text(json.dumps(summary, indent=2))
