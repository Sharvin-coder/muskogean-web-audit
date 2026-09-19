# Data Sources & Licenses

| Source | What | License / terms | Local location |
|---|---|---|---|
| HuggingFaceFW/fineweb-2 | cho_Latn, mus_Latn subsets (kept + removed), parquet | ODC-By 1.0, subject to CommonCrawl ToU | data/raw/HuggingFaceFW__fineweb-2/ (not committed) |
| cis-lmu/GlotCC-V1 | cho-Latn subset, parquet | CC0 metadata; content subject to CommonCrawl ToU | data/raw/cis-lmu__GlotCC-V1/ (not committed) |
| cis-lmu/glotlid model.bin (v3) | LID model | Apache 2.0 | local model cache (not committed; set GLOTLID_MODEL) |
| omniglot.com writing pages (chickasaw, koasati, mikasuki, creek, choctaw) | language sample texts, fetched 2026-08-11 | © Omniglot; used for research quotation, not redistributed | data/seed_pages/ (not committed) |
| native-languages.org vocabulary pages (alabama, koasati, mikasuki) | wordlists, fetched 2026-08-11 | © Native Languages of the Americas; research use, not redistributed | data/seed_pages/ (not committed) |
| Corpus metadata (HF API), OSCAR language table | presence census inputs | public metadata | queried live by src/corpus_presence.py |

Ethics posture: the repo commits only annotations, URLs, and derived
statistics — never scraped text (see paper Ethics Statement; CARE principles).
