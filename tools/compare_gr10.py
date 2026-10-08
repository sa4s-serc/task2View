"""Check whether relations drawn in GR10's UML are present in its Java code.

Run from the Task2View root. The model and the source were translated to English
separately, so a UML name that does not match a code class is reported as
non-code / unjudgeable rather than as contradicted.
"""

import sys
import unicodedata

sys.path.insert(0, "tools")
from java_facts import JavaFacts  # noqa: E402
from vpp_extract import VppModel  # noqa: E402

GR10 = "data/progetto_ing_software_gr10-main-English"
VPP = f"{GR10}/docs/visual-paradigm/Software_Engineering_Project_GR10_English.vpp"
SRC = f"{GR10}/src/main/java"
PACKAGES = {"Boundary", "Control", "Entity", "Database"}


def norm(s):
    if not s:
        return s
    s = unicodedata.normalize("NFKD", s.strip()).encode("ascii", "ignore").decode()
    return s[:-1] if s.endswith("2") else s


def main():
    m = VppModel(VPP)
    jf = JavaFacts(SRC)
    pkg_members = {
        p: {c for c, meta in jf.classes.items() if meta["path"].split("/")[0] == p}
        for p in PACKAGES
    }

    def resolve(n):
        """UML name -> set of code classes it stands for (package names fan out)."""
        n = norm(n)
        if n in pkg_members:
            return pkg_members[n]
        return {n} if n in jf.classes else set()

    def supported(src, tgt, kind):
        s_set, t_set = resolve(src), resolve(tgt)
        if not s_set or not t_set:
            return None  # not implemented; cannot be judged against code
        for a in s_set:
            for b in t_set:
                if kind in ("generalization", "realization"):
                    # VP orders these supertype -> subtype
                    if jf.extends.get(b) == a or a in jf.implements.get(b, ()):
                        return True
                elif jf.uses(a, b):
                    return True
        return False

    print("=" * 84)
    print("A. ALL CLASS DIAGRAMS vs code")
    print("=" * 84)
    misses = []
    for d in sorted(
        (x for x in m.diagrams.values() if x["type"] == "ClassDiagram"), key=lambda x: x["name"]
    ):
        rels = m.class_relations(d["id"])
        ok = bad = na = 0
        for r in rels:
            st = supported(r["source"], r["target"], r["kind"])
            if st is True:
                ok += 1
            elif st is False:
                bad += 1
                misses.append((d["name"], r))
            else:
                na += 1
        diag_cls = {norm(c["name"]) for c in m.members(d["id"], {"Class"})}
        impl = diag_cls & set(jf.classes)
        judged = ok + bad
        rate = f"{ok / judged:.0%}" if judged else "-"
        print(f"\n  {d['name']}")
        print(f"    classes {len(diag_cls):3d} (implemented {len(impl):3d}, analysis-only {len(diag_cls) - len(impl):3d})")
        print(f"    relations {len(rels):3d} -> confirmed {ok:3d}  contradicted {bad:3d}"
              f"  unjudgeable {na:3d}   precision {rate}")

    if misses:
        print("\n  contradicted relations:")
        for dn, r in misses:
            print(f"    [{dn}] {r['kind']} {r['source']} -> {r['target']}")

    print()
    print("=" * 84)
    print("B. ALL SEQUENCE DIAGRAMS vs code call graph")
    print("=" * 84)
    tot_ok = tot_bad = tot_self = tot_actor = tot_na = 0
    seq_misses = []
    for d in sorted(
        (x for x in m.diagrams.values() if x["type"] == "InteractionDiagram"),
        key=lambda x: x["name"],
    ):
        msgs = [x for x in m.messages(d["id"]) if not x["is_return"]]
        ok = bad = slf = actor = na = 0
        for x in msgs:
            s, t = norm(x["source"]), norm(x["target"])
            if x["source_kind"] == "actor" or x["target_kind"] == "actor":
                actor += 1
            elif s == t:
                slf += 1
            elif s not in jf.classes or t not in jf.classes:
                na += 1
            elif t in jf.call_targets(s) or jf.uses(s, t):
                ok += 1
            else:
                bad += 1
                seq_misses.append((d["name"], x))
        tot_ok += ok; tot_bad += bad; tot_self += slf; tot_actor += actor; tot_na += na
        judged = ok + bad
        rate = f"{ok / judged:.0%}" if judged else "-"
        print(f"  {rate:>5s}  ok {ok:3d} bad {bad:2d} self {slf:3d} actor {actor:2d} n/a {na:2d}"
              f"   {d['name']}")

    judged = tot_ok + tot_bad
    print(f"\n  TOTAL call messages judged {judged} | confirmed {tot_ok} | contradicted {tot_bad}")
    print(f"  excluded: self-calls {tot_self}, actor messages {tot_actor}, "
          f"non-code participants {tot_na}")
    if judged:
        print(f"  precision over judgeable messages: {tot_ok}/{judged} = {tot_ok / judged:.0%}")
    if seq_misses:
        print("\n  contradicted messages:")
        for dn, x in seq_misses:
            print(f"    [{dn}] {x['seq']:>12s} {x['source']} -> {x['target']}")


if __name__ == "__main__":
    main()
