"""Generate every LaTeX table in the paper from results/*.json.

No number in the paper is hand-typed: tables are \\input{} fragments
written by this script.
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RES = ROOT / "results"
OUT = ROOT / "paper" / "tables"
OUT.mkdir(parents=True, exist_ok=True)

CODES = ["cho", "cic", "mus", "akz", "cku", "mik"]


def load(name):
    return json.loads((RES / name).read_text())


# ---------- Table 1: corpus presence ----------
pres = load("corpus_presence.json")
NAMES = {
    "allenai/c4": "C4/mC4",
    "statmt/cc100": "CC-100",
    "oscar-corpus/OSCAR-2301": "OSCAR 23.01",
    "allenai/MADLAD-400": "MADLAD-400",
    "HPLT/HPLT2.0_cleaned": "HPLT 2.0",
    "cis-lmu/GlotCC-V1": "GlotCC-V1",
    "HuggingFaceFW/fineweb-2": "FineWeb-2",
}
rows = []
for repo, disp in NAMES.items():
    v = pres[repo]
    marks = " & ".join(
        r"\ding{51}" if c in v["muskogean"] else "--" for c in CODES)
    rows.append(f"{disp} & {v['n_langs']} & {marks} \\\\")
(OUT / "corpus_presence.tex").write_text(
    "\\setlength{\\tabcolsep}{3.2pt}\n"
    "\\begin{tabular}{lrcccccc}\n\\toprule\n"
    "Corpus & Langs & \\textit{cho} & \\textit{cic} & \\textit{mus} & "
    "\\textit{akz} & \\textit{cku} & \\textit{mik} \\\\\n\\midrule\n"
    + "\n".join(rows) + "\n\\bottomrule\n\\end{tabular}\n")

# ---------- Table 2: kept-document audit ----------
audit = load("audit_kept.json")
SUB = {"fw2_cho": "FW2 \\textit{cho}", "fw2_mus": "FW2 \\textit{mus}",
       "glotcc_cho": "GlotCC \\textit{cho}"}
rows = []
for k, disp in SUB.items():
    s = audit["per_subset"][k]
    yes = s["is_target"].get("yes", 0)
    rows.append(
        f"{disp} & {s['n_docs']} & {s['n_content_clusters']} & {yes} & "
        f"{round(100*s['religious_char_frac'])}\\% & "
        f"{round(100*s['contemporary_char_frac'])}\\% \\\\")
(OUT / "audit_kept.tex").write_text(
    "\\setlength{\\tabcolsep}{3.2pt}\n"
    "\\begin{tabular}{lrrrrr}\n\\toprule\n"
    "Subset & Docs & Texts & Maj. & Relig. & Cont. \\\\\n"
    " & & & target & chars & chars \\\\\n\\midrule\n"
    + "\n".join(rows) + "\n\\bottomrule\n\\end{tabular}\n")

# ---------- Table 3: removed piles ----------
rem = load("removed_analysis.json")
gen = load("removed_genuine.json")
rows = []
for lang in ("cho", "mus"):
    r = rem[f"{lang}_Latn_removed"]
    g = gen[lang]
    rows.append(
        f"\\textit{{{lang}}} & {r['n_docs']:,} & {r['median_chars']} & "
        f"{round(100*r['still_target_frac'], 1)}\\% & "
        f"{g['genuine_unique_urls']} & "
        f"{g['kept_docs_for_reference']} \\\\")
(OUT / "removed.tex").write_text(
    "\\setlength{\\tabcolsep}{3.2pt}\n"
    "\\begin{tabular}{lrrrrr}\n\\toprule\n"
    "Lang & Removed & Med. & Still targ. & Genuine & Kept \\\\\n"
    " & docs & chars & (GlotLID v3) & lost & docs \\\\\n\\midrule\n"
    + "\n".join(rows) + "\n\\bottomrule\n\\end{tabular}\n")

# ---------- Table 4: LID stress test ----------
lid = load("lid_stress.json")
per = lid["per_segment"]
LANGNAME = {"cho": "Choctaw", "mus": "Muscogee", "cic": "Chickasaw",
            "akz": "Alabama", "cku": "Koasati", "mik": "Mikasuki"}
rows = []
for lang in ("cho", "mus"):
    segs = [r for r in per if r["lang"] == lang]
    n = len(segs)
    full = sum(r["full_correct"] for r in segs)
    nod = sum(r["no_diacrit_correct"] for r in segs)
    chunk = sum(r["chunks8_recall"] for r in segs) / n
    rows.append(
        f"{LANGNAME[lang]} & \\textit{{{lang}}}\\_Latn & {n} & {full}/{n} & "
        f"{nod}/{n} & {chunk:.2f} \\\\")
for lang in ("cic", "akz", "cku", "mik"):
    segs = [r for r in per if r["lang"] == lang]
    # report the as-crawled segment (first) for languages without a label
    top, prob = segs[0]["full"][0]
    top_esc = top.replace("_", r"\_")
    rows.append(
        f"{LANGNAME[lang]} & \\emph{{none}} & {len(segs)} & "
        f"\\multicolumn{{3}}{{l}}{{$\\rightarrow$ {top_esc} "
        f"({prob:.2f})}} \\\\")
(OUT / "lid_stress.tex").write_text(
    "\\setlength{\\tabcolsep}{3.0pt}\n"
    "\\begin{tabular}{llrrrr}\n\\toprule\n"
    "Language & Label & Segs & Full & No diac. & Frag. \\\\\n\\midrule\n"
    + "\n".join(rows) + "\n\\bottomrule\n\\end{tabular}\n")

print("wrote", len(list(OUT.glob("*.tex"))), "tables to", OUT)
