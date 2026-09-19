"""Build the recall-side seed set from verified web sources.

Every segment is extracted programmatically from either (a) the downloaded
corpus parquet files or (b) pages fetched by fetch_seed_pages.py — never
hand-typed. Writes data/seed/seed_segments.json.
"""

import json
import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PAGES = ROOT / "data" / "seed_pages"
OUT = ROOT / "data" / "seed"
OUT.mkdir(parents=True, exist_ok=True)

FW2 = ROOT / "data/raw/HuggingFaceFW__fineweb-2/data"


def parquet_text(subset: str, url_sub: str) -> str:
    df = pd.read_parquet(FW2 / subset / "train" / "000_00000.parquet")
    hits = df[df.url.str.contains(url_sub, regex=False)]
    assert len(hits) >= 1, f"no doc matching {url_sub} in {subset}"
    return hits.iloc[0].text, hits.iloc[0].url


def page_slice(fname: str, start: str, end: str) -> tuple[str, str]:
    raw = (PAGES / fname).read_text(encoding="utf-8")
    url = raw.splitlines()[0].lstrip("# ").strip()
    i = raw.index(start)
    j = raw.index(end, i)
    txt = re.sub(r"\s+", " ", raw[i:j]).strip()
    return txt, url


segments = []


def add(lang, name, text, url, seg_type, era, note=""):
    segments.append({
        "lang": lang, "name": name, "text": text.strip(), "url": url,
        "type": seg_type, "era": era, "note": note, "n_chars": len(text.strip()),
    })


# ---- Choctaw (cho) ----
t, u = parquet_text("cho_Latn", "cho.wikipedia.org/wiki/Ai")
add("cho", "udhr_art1", t.split("Atikel I")[1], u, "running", "20th c.",
    "UDHR Art. 1, headers removed")
t, u = parquet_text("cho_Latn", "jw.org/cho")
add("cho", "jw_modern", t, u, "running", "contemporary")
t, u = parquet_text("cho_Latn", "MRK.1.CHTW")
add("cho", "bible_abs", t[:1500], u, "running",
    "19th c. ABS portions (bible.com version id 1927)")
df = pd.read_parquet(FW2 / "cho_Latn_removed/train/000_00000.parquet")
aca = df[df.url.str.contains("touchstoneimaging.com", regex=False)].iloc[0]
add("cho", "aca_tagline", aca.text[:600], aca.url, "running", "contemporary",
    "ACA §1557 language-access notice, from removed pile")
school = df[df.url.str.contains("choctawschool.com", regex=False)].iloc[0]
add("cho", "school_lesson", school.text[:800], school.url, "wordlist",
    "contemporary", "Choctaw Nation language school, from removed pile")

# ---- Muscogee (mus) ----
t, u = page_slice("omniglot_creek.txt", "Este vtekat", "Gloss")
add("mus", "udhr_art1", t, u, "running", "20th c.", "UDHR Art. 1 (Omniglot)")
t, u = parquet_text("mus_Latn", "ekvn-yefolecv")
add("mus", "community_modern", t[:1000], u, "running", "contemporary")
t, u = parquet_text("mus_Latn", "languagegeek.com")
add("mus", "gouge_1915", t.split("Totkv Mocvse.")[1][:900],
    u, "running", "1915 (modernized orthography)")
dfm = pd.read_parquet(FW2 / "mus_Latn_removed/train/000_00000.parquet")
pr = dfm[dfm.url.str.contains("marysrosaries.com/Muskogee", regex=False)].iloc[0]
add("mus", "prayer", pr.text[:500], pr.url, "running", "19th-20th c.",
    "Lord's Prayer in Muscogee, from removed pile")

# ---- Chickasaw (cic) ----
t, u = page_slice("omniglot_chickasaw.txt", "Himmaka' nittakookano", "Translation")
add("cic", "udhr_art1", t, u, "running", "contemporary orthography",
    "UDHR Art. 1 (Omniglot); Munro-Willmond orthography")

t2 = re.sub(r"(\w) (\S) (\w)", r"\1\2\3", t)
t2 = re.sub(r"(\w) (\w)\b", r"\1\2", t2)
add("cic", "udhr_art1_cleaned", t2, u, "running", "contemporary orthography",
    "Same text with HTML-span spacing artifacts merged programmatically")

# ---- Koasati (cku) ----
t, u = page_slice("omniglot_koasati.txt", "Kowassaati sapha", "Kowassaati aatiha kosnap.")
add("cku", "poem", t + " Kowassaati aatiha kosnap.", u, "running", "contemporary")

# ---- Mikasuki (mik) ----
t, u = page_slice("omniglot_mikasuki.txt", "Enchew aa tke", "Translation")
add("mik", "creation_story", t, u, "running", "20th c.")

# ---- Alabama (akz) ----
raw = (PAGES / "nativelang_alabama.txt").read_text(encoding="utf-8")
url = raw.splitlines()[0].lstrip("# ").strip()
words = re.findall(
    r"^(Ch[áa]ff[àa]aka|T[òo]klo|T[óo]tch[ìi]ina|[ÓO]st[àa]aka|T[áa]łł[àa]api|Naani|Tayyi|Ifa|Hasi|.*)$",
    "", 0)  # placeholder, replaced below
# take the Alabama column: lines following each English gloss line
lines = raw.splitlines()
vocab = []
grab = False
for ln in lines:
    if ln.startswith("English ("):
        grab = True
        continue
    if grab and ln and "(" not in ln and not ln.startswith(("Click", "Back", "Sponsored")):
        vocab.append(ln.strip())
    if ln.startswith("Back to"):
        break
vocab = [v for v in vocab if v and v[0].isupper()][:40]
add("akz", "vocab_list", " ".join(vocab), url, "wordlist", "contemporary",
    "No running Alabama text locatable on the open web; 20-word basic vocabulary")

with open(OUT / "seed_segments.json", "w", encoding="utf-8") as f:
    json.dump(segments, f, ensure_ascii=False, indent=1)
for s in segments:
    print(s["lang"], s["name"], s["type"], s["n_chars"], "|", s["text"][:60])
