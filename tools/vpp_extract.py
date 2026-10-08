"""Extract a machine-readable model from a Visual Paradigm .vpp file.

A .vpp is a SQLite database whose MODEL_ELEMENT.DEFINITION column holds VP's own
nested text format. This module parses the subset needed for architecture-view
ground truth: class relations (association / generalization / dependency) and
sequence-diagram messages with their ordering.
"""

import re
import sqlite3
from collections import defaultdict

# VP references look like <a:b:c> or <a:b$c>; the element itself is the last segment.
REF = re.compile(r"<([^<>]+)>")
BLOCK = re.compile(r"(\w+)=\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}", re.S)


def _tail(ref: str) -> str:
    return re.split(r"[:$]", ref.strip())[-1]


def _attr(text: str, key: str):
    m = re.search(rf'\b{key}=(?:"([^"]*)"|<([^>]+)>|([^;\n]+));', text)
    if not m:
        return None
    return m.group(1) or (_tail(m.group(2)) if m.group(2) else (m.group(3) or "").strip())


class VppModel:
    def __init__(self, path: str):
        self.db = sqlite3.connect(path)
        self.elements = {}
        for eid, mtype, name, definition in self.db.execute(
            "select ID, MODEL_TYPE, NAME, DEFINITION from MODEL_ELEMENT"
        ):
            self.elements[eid] = {
                "id": eid,
                "type": mtype,
                "name": name,
                "def": (definition or b"").decode("utf8", "replace")
                if isinstance(definition, bytes)
                else (definition or ""),
            }
        self.diagrams = {
            did: {"id": did, "type": dtype, "name": name}
            for did, dtype, name in self.db.execute("select ID, DIAGRAM_TYPE, NAME from DIAGRAM")
        }
        self._members = defaultdict(set)
        for did, mid in self.db.execute(
            "select DIAGRAM_ID, MODEL_ELEMENT_ID from DIAGRAM_ELEMENT where MODEL_ELEMENT_ID is not null"
        ):
            self._members[did].add(mid)

    def name_of(self, eid):
        e = self.elements.get(eid)
        return e["name"] if e else None

    def diagram_by_name(self, name):
        for d in self.diagrams.values():
            if d["name"] == name:
                return d
        raise KeyError(name)

    def members(self, diagram_id, of_type=None):
        ids = self._members[diagram_id]
        return [
            self.elements[i]
            for i in ids
            if i in self.elements and (of_type is None or self.elements[i]["type"] in of_type)
        ]

    def _ends(self, text):
        """Return the from/to sub-blocks of a relationship definition."""
        return {k: v for k, v in BLOCK.findall(text) if k in ("from", "to")}

    def class_relations(self, diagram_id):
        """Associations, generalizations and dependencies drawn on a class diagram."""
        out = []
        for e in self.members(
            diagram_id, {"Association", "Generalization", "Dependency", "Realization", "Usage"}
        ):
            d = e["def"]
            if e["type"] == "Association":
                ends = self._ends(d)
                if not {"from", "to"} <= ends.keys():
                    continue
                src, tgt = _attr(ends["from"], "type"), _attr(ends["to"], "type")
                out.append(
                    {
                        "kind": "association",
                        "source": self.name_of(src),
                        "target": self.name_of(tgt),
                        "source_mult": _attr(ends["from"], "multiplicity"),
                        "target_mult": _attr(ends["to"], "multiplicity"),
                        "aggregation": _attr(ends["from"], "aggregationKind")
                        or _attr(ends["to"], "aggregationKind"),
                        "label": e["name"],
                    }
                )
            else:
                src, tgt = _attr(d, "fromModel"), _attr(d, "toModel")
                out.append(
                    {
                        "kind": e["type"].lower(),
                        "source": self.name_of(src),
                        "target": self.name_of(tgt),
                        "label": e["name"],
                    }
                )
        return [r for r in out if r["source"] and r["target"]]

    def _participant(self, eid):
        """Resolve a lifeline / actor to the classifier it stands for.

        Returns (lifeline_name, classifier_name, kind). Actor names can collide
        with class names, so callers must not treat an actor as a class.
        """
        e = self.elements.get(eid)
        if not e:
            return None, None, None
        if e["type"] == "InteractionLifeLine":
            return e["name"], self.name_of(_attr(e["def"], "baseClassifier")), "class"
        if e["type"] == "InteractionActor":
            return e["name"], self.name_of(_attr(e["def"], "referencedActor")), "actor"
        return e["name"], None, e["type"]

    @staticmethod
    def _seq_key(sn):
        return tuple(int(p) if p.isdigit() else 0 for p in re.split(r"\D+", sn or "0") if p != "")

    def messages(self, diagram_id):
        """Ordered messages of a sequence diagram."""
        out = []
        for e in self.members(diagram_id, {"Message"}):
            ends = self._ends(e["def"])
            if not {"from", "to"} <= ends.keys():
                continue
            s_life = _attr(ends["from"], "EndModelElement")
            t_life = _attr(ends["to"], "EndModelElement")
            s_name, s_class, s_kind = self._participant(s_life)
            t_name, t_class, t_kind = self._participant(t_life)
            sn = _attr(e["def"], "sequenceNumber")
            # Call messages carry the invoked operation by reference; only return
            # messages put their payload in NAME.
            op = _attr(e["def"], "operation")
            out.append(
                {
                    "seq": sn,
                    "message": e["name"] or self.name_of(op),
                    "operation": self.name_of(op),
                    "is_return": op is None and bool(e["name"]),
                    "source": s_class or s_name,
                    "target": t_class or t_name,
                    "source_lifeline": s_name,
                    "target_lifeline": t_name,
                    "source_kind": s_kind,
                    "target_kind": t_kind,
                }
            )
        return sorted(out, key=lambda m: self._seq_key(m["seq"]))
