"""Measure Phase 3 (candidate repository area selection) recall on GR10.

Ground truth: the participants of each BCED sequence diagram, which we already
verified are all present in the code. A scoping strategy "succeeds" for a view
only if it selects every participant that view needs -- a single missed
participant makes the corresponding interaction ungeneratable in Phase 4.

Strategies compared:
  name      file-name keyword match (what the pipeline document describes)
  content   name match plus full-text keyword grep
  name+1hop name match plus one hop over the static call graph
  content+1hop  content match plus one hop
"""

import os
import re
import sys
import unicodedata

sys.path.insert(0, "tools")
from java_facts import JavaFacts  # noqa: E402
from vpp_extract import VppModel  # noqa: E402

VPP = "italian/progetto_ing_software_gr10-main/docs/visual-paradigm/Progetto_Ing_Software_GR10.vpp"
SRC = "italian/progetto_ing_software_gr10-main/src/main/java"
STOP = {"di", "del", "della", "al", "il", "la", "le", "elenco", "pattern", "bced",
        "nuova", "nuovo", "informazioni", "dettagli", "andamento"}


def norm(s):
    if not s:
        return s
    s = unicodedata.normalize("NFKD", s.strip()).encode("ascii", "ignore").decode()
    return s[:-1] if s.endswith("2") else s


def stem(w):
    """Crude Italian stemmer: keep the discriminative prefix of a cue word."""
    return norm(w).lower()[:6]


def main():
    m = VppModel(VPP)
    jf = JavaFacts(SRC)
    sources = {
        c: open(os.path.join(SRC, jf.classes[c]["path"]), encoding="utf8",
                errors="replace").read().lower()
        for c in jf.classes
    }
    # one hop over the union of call and structural edges
    neighbours = {
        c: {d for d in jf.classes if d != c and (jf.uses(c, d) or jf.uses(d, c))}
        for c in jf.classes
    }

    def cues_from(name):
        words = re.split(r"[^\w]+", norm(name))
        return {stem(w) for w in words if w and w.lower() not in STOP and len(w) > 3}

    def select(cues, mode):
        picked = set()
        for c in jf.classes:
            hay_name = norm(c).lower()
            hit = any(q in hay_name for q in cues)
            if not hit and mode == "content":
                hit = any(q in sources[c] for q in cues)
            if hit:
                picked.add(c)
        return picked

    rows = []
    for d in sorted(
        (x for x in m.diagrams.values()
         if x["type"] == "InteractionDiagram" and "BCED" in x["name"]),
        key=lambda x: x["name"],
    ):
        truth = set()
        for msg in m.messages(d["id"]):
            for side in ("source", "target"):
                if msg[f"{side}_kind"] == "class":
                    n = norm(msg[side])
                    if n in jf.classes:
                        truth.add(n)
        if not truth:
            continue
        cues = cues_from(d["name"])
        res = {}
        for mode in ("name", "content"):
            base = select(cues, mode)
            res[mode] = base
            res[mode + "+1hop"] = base | {n for c in base for n in neighbours[c]}
        rows.append((d["name"], cues, truth, res))

    strategies = ["name", "name+1hop", "content", "content+1hop"]
    print(f"{'view (BCED sequence)':<46}{'|GT|':>5}", end="")
    for s in strategies:
        print(f"{s:>15}", end="")
    print()
    print("-" * 46 + "-" * 5 + "-" * 60)

    agg = {s: [0, 0, 0] for s in strategies}  # found, total, complete-views
    for name, cues, truth, res in rows:
        print(f"{name[:44]:<46}{len(truth):>5}", end="")
        for s in strategies:
            sel = res[s]
            found = len(truth & sel)
            agg[s][0] += found
            agg[s][1] += len(truth)
            agg[s][2] += 1 if found == len(truth) else 0
            print(f"{found}/{len(truth)} ({len(sel):2d}f)".rjust(15), end="")
        print()

    print("\n" + "=" * 106)
    print(f"{'STRATEGY':<16}{'participant recall':>22}{'views fully covered':>24}"
          f"{'mean files selected':>24}")
    for s in strategies:
        found, total, complete = agg[s]
        mean_files = sum(len(r[3][s]) for r in rows) / len(rows)
        print(f"{s:<16}{f'{found}/{total} = {found / total:.0%}':>22}"
              f"{f'{complete}/{len(rows)}':>24}{f'{mean_files:.1f} / {len(jf.classes)}':>24}")

    print("\nmissed participants (name-only strategy):")
    for name, cues, truth, res in rows:
        missed = sorted(truth - res["name"])
        if missed:
            print(f"  {name[:44]:<46} cues={sorted(cues)}")
            print(f"  {'':<46} missed: {missed}")


if __name__ == "__main__":
    main()
