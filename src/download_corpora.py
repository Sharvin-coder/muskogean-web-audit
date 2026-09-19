"""Download every corpus subset labeled as a Muskogean language.

Targets (checked 2026-08-11 via HF API):
  - HuggingFaceFW/fineweb-2: data/cho_Latn, data/cho_Latn_removed,
    data/mus_Latn, data/mus_Latn_removed
  - cis-lmu/GlotCC-V1: v1.0/cho-Latn
No corpus carries cic (Chickasaw), akz (Alabama), cku (Koasati), or
mik (Mikasuki) subsets; that absence is itself a finding.
"""

import json
from pathlib import Path

from huggingface_hub import HfApi, hf_hub_download

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"

TARGETS = {
    "HuggingFaceFW/fineweb-2": [
        "data/cho_Latn",
        "data/cho_Latn_removed",
        "data/mus_Latn",
        "data/mus_Latn_removed",
    ],
    "cis-lmu/GlotCC-V1": [
        "v1.0/cho-Latn",
    ],
}


def main() -> None:
    api = HfApi()
    manifest = []
    for repo, folders in TARGETS.items():
        for folder in folders:
            files = [
                f
                for f in api.list_repo_tree(
                    repo, folder, repo_type="dataset", recursive=True
                )
                if getattr(f, "size", None) is not None
            ]
            for f in files:
                local = hf_hub_download(
                    repo_id=repo,
                    filename=f.path,
                    repo_type="dataset",
                    local_dir=RAW / repo.replace("/", "__"),
                )
                manifest.append(
                    {"repo": repo, "path": f.path, "size": f.size, "local": local}
                )
                print(f"{repo}\t{f.path}\t{f.size:,} bytes")
    out = RAW / "manifest.json"
    out.write_text(json.dumps(manifest, indent=2))
    print(f"\n{len(manifest)} files -> {out}")


if __name__ == "__main__":
    main()
