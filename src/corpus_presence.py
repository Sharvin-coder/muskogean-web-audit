"""Which major web-crawled corpora claim ANY Muskogean language subset?

Checks HF metadata/file trees programmatically. OSCAR 23.01 is gated on HF, so
its negative is taken from the project's public language table (URL below,
verified 2026-08-11: 151 languages, no Muskogean).

Writes results/corpus_presence.json.
"""

import json
import re
from pathlib import Path

import requests
from huggingface_hub import HfApi

ROOT = Path(__file__).resolve().parents[1]
CODES = ("cho", "cic", "mus", "akz", "cku", "mik")
API = "https://huggingface.co/api/datasets/{}"


def tag_langs(repo: str) -> list[str]:
    tags = requests.get(API.format(repo), timeout=30).json().get("tags", [])
    return sorted({t.split(":", 1)[1] for t in tags if re.fullmatch(r"language:[a-z]{2,3}", t)})


def tree_langs(repo: str, folder: str) -> list[str]:
    api = HfApi()
    names = [
        f.path.split("/")[-1]
        for f in api.list_repo_tree(repo, folder, repo_type="dataset", recursive=False)
    ]
    return sorted({n.split("_")[0].split("-")[0] for n in names})


def main() -> None:
    results = {}

    for repo in ("HuggingFaceFW/fineweb-2", "cis-lmu/GlotCC-V1", "allenai/c4",
                 "HPLT/HPLT2.0_cleaned", "statmt/cc100"):
        langs = tag_langs(repo)
        results[repo] = {
            "method": "hf_language_tags",
            "n_langs": len(langs),
            "muskogean": sorted(set(langs) & set(CODES)),
        }

    langs = tree_langs("allenai/MADLAD-400", "data")
    results["allenai/MADLAD-400"] = {
        "method": "hf_file_tree",
        "n_langs": len(langs),
        "muskogean": sorted(set(langs) & set(CODES)),
    }

    results["oscar-corpus/OSCAR-2301"] = {
        "method": "project_documentation",
        "source": "https://oscar-project.github.io/documentation/versions/oscar-2301/",
        "n_langs": 151,
        "muskogean": [],
        "note": "gated on HF; language table verified manually 2026-08-11",
    }

    out = ROOT / "results" / "corpus_presence.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(results, indent=2))
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
