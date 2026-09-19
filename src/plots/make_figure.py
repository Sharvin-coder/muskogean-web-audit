"""Figure 1: genre composition (characters) of every kept Muskogean document.

Palette validated with the dataviz six-checks validator (all PASS, light mode,
2026-08-11): lightness band, chroma floor, CVD separation (worst adjacent
protan dE 8.8 with gap+legend secondary encoding), normal-vision floor,
contrast (one WARN relieved by legend labels + Table 2 as table view).
Vector PDF + PNG proof. Reads results/ + audit annotations.
"""

import json
from collections import defaultdict
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[2]
docs = {d["doc_id"]: d for d in json.loads(
    (ROOT / "data/audit/kept_docs_full.json").read_text(encoding="utf-8"))}
ann = json.loads((ROOT / "data/audit/annotations_kept.json").read_text(
    encoding="utf-8"))["docs"]

GENRES = ["bible", "religious-org", "wiki-canonical", "udhr",
          "gb-index-terms", "wordlist-phrases", "traditional-story", "community"]
LABELS = {"bible": "Bible translation", "religious-org": "Religious org.",
          "wiki-canonical": "Wiki canonical text", "udhr": "UDHR Art. 1",
          "gb-index-terms": "Google Books index terms",
          "wordlist-phrases": "Phrase list", "traditional-story":
          "Traditional story", "community": "Community (living use)"}
# validated palette (see docstring); fixed assignment, never cycled
COLORS = ["#005A96", "#5AA9DC", "#008A64", "#9C8A00",
          "#6E5EC1", "#C98300", "#AD4F87", "#8F3B00"]

SUBS = [("glotcc_cho", "GlotCC-V1 cho"), ("fw2_cho", "FineWeb-2 cho"),
        ("fw2_mus", "FineWeb-2 mus")]

INK = "#333333"
MUTED = "#666666"


def subset(doc_id):
    return "glotcc_cho" if doc_id.startswith("glotcc") else (
        "fw2_cho" if "_cho" in doc_id else "fw2_mus")


chars = defaultdict(lambda: defaultdict(int))
for a in ann:
    chars[subset(a["doc_id"])][a["genre"]] += len(docs[a["doc_id"]]["text"])

fig, ax = plt.subplots(figsize=(6.2, 3.1))
fig.subplots_adjust(left=0.155, right=0.975, top=0.97, bottom=0.46)
ypos = range(len(SUBS))
left = [0.0] * len(SUBS)
for g, c in zip(GENRES, COLORS):
    vals = [chars[s][g] / 1000 for s, _ in SUBS]
    ax.barh(list(ypos), vals, left=left, color=c, label=LABELS[g],
            height=0.62, edgecolor="white", linewidth=0.8)
    left = [l + v for l, v in zip(left, vals)]

for y, total in zip(ypos, left):
    ax.text(total + 0.5, y, f"{total:.1f}k", va="center", ha="left",
            fontsize=8, color=MUTED)

ax.set_yticks(list(ypos), [d for _, d in SUBS], fontsize=9, color=INK)
ax.set_xlabel("thousand characters (all kept documents)", fontsize=9,
              color=INK)
ax.set_xlim(0, max(left) * 1.09)
ax.tick_params(labelsize=8, colors=INK, length=0)
ax.set_axisbelow(True)
ax.grid(axis="x", color="#DDDDDD", linewidth=0.6)
ax.spines[["top", "right", "left"]].set_visible(False)
ax.spines["bottom"].set_color("#BBBBBB")
fig.legend(fontsize=7.5, ncol=2, frameon=False, loc="lower center",
           bbox_to_anchor=(0.53, 0.01), handlelength=1.2, columnspacing=1.4,
           labelcolor=INK)
out = ROOT / "figures"
out.mkdir(exist_ok=True)
fig.savefig(out / "genre_composition.pdf", bbox_inches="tight")
fig.savefig(out / "genre_composition.png", bbox_inches="tight", dpi=160)
print("wrote", out / "genre_composition.pdf")
