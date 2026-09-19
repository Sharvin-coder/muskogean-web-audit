"""Fetch candidate seed pages for the recall-side experiment.

Saves raw text extractions to data/seed_pages/ for manual curation of
target-language segments. Fetched 2026-08-11.
"""

import re
from html import unescape
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "seed_pages"
OUT.mkdir(parents=True, exist_ok=True)

URLS = {
    "udhr_cic_unicode": "https://www.unicode.org/udhr/d/udhr_cic.html",
    "omniglot_chickasaw": "https://omniglot.com/writing/chickasaw.htm",
    "omniglot_alabama": "https://omniglot.com/writing/alabama.htm",
    "omniglot_koasati": "https://omniglot.com/writing/koasati.htm",
    "omniglot_mikasuki": "https://omniglot.com/writing/mikasuki.htm",
    "omniglot_choctaw": "https://omniglot.com/writing/choctaw.htm",
    "omniglot_creek": "https://omniglot.com/writing/creek.htm",
    "nativelang_alabama": "https://www.native-languages.org/alabama_words.htm",
    "nativelang_koasati": "https://www.native-languages.org/koasati_words.htm",
    "nativelang_mikasuki": "https://www.native-languages.org/mikasuki_words.htm",
}

TAG = re.compile(r"<(script|style)[^>]*>.*?</\1>", re.S | re.I)
ANY = re.compile(r"<[^>]+>")


def to_text(html: str) -> str:
    html = TAG.sub(" ", html)
    html = re.sub(r"<(br|/p|/div|/tr|/li|/h[1-6])[^>]*>", "\n", html, flags=re.I)
    txt = unescape(ANY.sub(" ", html))
    lines = [re.sub(r"[ \t]+", " ", ln).strip() for ln in txt.splitlines()]
    return "\n".join(ln for ln in lines if ln)


for name, url in URLS.items():
    try:
        r = requests.get(url, timeout=30, headers={"User-Agent": "Mozilla/5.0"})
        r.raise_for_status()
        r.encoding = r.apparent_encoding or r.encoding
        (OUT / f"{name}.txt").write_text(
            f"# {url}\n" + to_text(r.text), encoding="utf-8")
        print("ok ", name, len(r.text))
    except Exception as e:  # noqa: BLE001 — log-and-continue fetch loop
        print("FAIL", name, e)
