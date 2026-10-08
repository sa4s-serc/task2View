"""Facts derived from the parsed repository: entities, deploy and build units,
layers, entry points, and the repository signals used by the viewpoint catalog.

Every rule is general (annotations, file kinds, library markers in corpus.yaml);
none refers to a particular repository. Each signal keeps the evidence that
raised it, so a reader can check why a style viewpoint was offered.
"""

from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from pathlib import Path

import yaml

from task2view.contracts.card import BuildUnit, DeployUnit, Edge, Entity, EntityField, EntryPoint, RepositoryCard, Symbol

_SQL_TABLE = re.compile(r"create\s+table\s+(?:if\s+not\s+exists\s+)?[`\"\[]?([\w.]+)[`\"\]]?\s*\((.*?)\)\s*;", re.I | re.S)
_SQL_FK = re.compile(r"foreign\s+key\s*\(\s*[`\"]?(\w+)[`\"]?\s*\)\s*references\s+[`\"]?([\w.]+)", re.I)
_SQL_INLINE_REF = re.compile(r"^[`\"]?(\w+)[`\"]?\s+[\w()]+.*?references\s+[`\"]?([\w.]+)", re.I)
_PY_ORM_BASES = {"Base", "DeclarativeBase", "Model", "models.Model", "db.Model", "SQLModel", "Document"}
_PY_RELATIONS = {"relationship": "relation", "ForeignKey": "many-to-one", "models.ForeignKey": "many-to-one",
                 "models.OneToOneField": "one-to-one", "models.ManyToManyField": "many-to-many"}


def _ann(name: str) -> str:
    return name.split("(", 1)[0]


def _ann_arg(annotation: str, key: str) -> str | None:
    m = re.search(rf"{key}\s*=\s*\"([^\"]+)\"", annotation)
    return m.group(1) if m else None


# ----------------------------------------------------------------- entities

def entities_from_symbols(symbols: dict[str, Symbol], edges: list[Edge], rules: dict) -> list[Entity]:
    entity_anns = set(rules["markers"]["entity-annotations"])
    relation_anns = rules["markers"]["relation-annotations"]
    key_anns = set(rules["markers"]["key-annotations"])
    field_targets: dict[tuple[str, str], str] = {}
    for e in edges:
        if e.kind == "field":
            field_targets.setdefault((e.source, e.detail), e.target)
    out: list[Entity] = []
    for s in symbols.values():
        if s.is_test:
            continue
        names = {_ann(a) for a in s.annotations}
        is_java_entity = s.language == "java" and bool(names & (entity_anns - {"Table"}))
        is_py_model = s.language == "python" and s.kind == "class" and any(b in _PY_ORM_BASES for b in s.extends)
        if not (is_java_entity or is_py_model):
            continue
        table = next((_ann_arg(a, "name") for a in s.annotations if _ann(a) == "Table"), None)
        entity = Entity(symbol=s.id, name=s.name, table=table, source="orm", file=s.file)
        for f in s.fields:
            fanns = {_ann(a) for a in f.annotations}
            if f.static or "Transient" in fanns:
                continue  # not persisted under any ORM convention
            relation = next((relation_anns[a] for a in fanns if a in relation_anns), None)
            if relation is None and s.language == "python" and f.type:
                relation = next((v for k, v in _PY_RELATIONS.items() if f.type.endswith(k)), None)
            target = field_targets.get((s.id, f.name))
            fk = next((_ann_arg(a, "name") for a in f.annotations if _ann(a) == "JoinColumn"), None)
            entity.fields.append(EntityField(
                name=f.name, type=f.type, key=bool(fanns & key_anns),
                relation=relation if (relation or target) else None, target=target if relation else None,
                foreign_key=fk,
            ))
        out.append(entity)
    return out


def entities_from_schema(files: list[tuple[Path, str]]) -> list[Entity]:
    out: list[Entity] = []
    for path, rel in files:
        try:
            sql = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for m in _SQL_TABLE.finditer(sql):
            table, body = m.group(1), m.group(2)
            entity = Entity(name=table.split(".")[-1], table=table, source="schema", file=rel)
            fks = {col.lower(): ref for col, ref in _SQL_FK.findall(body)}
            for raw in re.split(r",\s*(?![^()]*\))", body):
                line = raw.strip()
                low = line.lower()
                if not line or low.startswith(("primary key", "foreign key", "constraint", "unique", "key ", "index")):
                    continue
                parts = line.split()
                col = parts[0].strip('`"[]')
                inline = _SQL_INLINE_REF.match(line)
                ref = fks.get(col.lower()) or (inline.group(2) if inline else None)
                entity.fields.append(EntityField(
                    name=col, type=parts[1] if len(parts) > 1 else None, key="primary key" in low,
                    relation="many-to-one" if ref else None, target=None, foreign_key=col if ref else None,
                ))
            for pk in re.findall(r"primary\s+key\s*\(([^)]*)\)", body, re.I):
                for col in (c.strip(' `"') for c in pk.split(",")):
                    for f in entity.fields:
                        if f.name == col:
                            f.key = True
            out.append(entity)
    return out


# ------------------------------------------------------------ deploy / build

def deploy_units(files: list[tuple[Path, str]]) -> list[DeployUnit]:
    out: list[DeployUnit] = []
    for path, rel in files:
        name = path.name.lower()
        try:
            content = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if name.startswith("dockerfile") or name.endswith(".dockerfile"):
            details = {k.lower(): [l.split(None, 1)[1].strip() for l in content.splitlines()
                                   if l.upper().startswith(k + " ") and len(l.split(None, 1)) > 1]
                       for k in ("FROM", "EXPOSE", "CMD", "ENTRYPOINT")}
            out.append(DeployUnit(kind="dockerfile", name=rel, file=rel, details={k: v for k, v in details.items() if v}))
        elif name.endswith((".yml", ".yaml")) and ("compose" in name or "services:" in content):
            try:
                doc = yaml.safe_load(content) or {}
            except yaml.YAMLError:
                continue
            if isinstance(doc, dict) and isinstance(doc.get("services"), dict):
                for svc, spec in doc["services"].items():
                    spec = spec or {}
                    details = {
                        "image": str(spec.get("image", "")), "build": str(spec.get("build", "")) if spec.get("build") else "",
                        "ports": [str(p) for p in spec.get("ports", []) or []],
                        "depends_on": list(spec.get("depends_on", []) or []) if not isinstance(spec.get("depends_on"), dict) else list(spec["depends_on"]),
                    }
                    out.append(DeployUnit(kind="compose-service", name=str(svc), file=rel, details={k: v for k, v in details.items() if v}))
            elif isinstance(doc, dict) and doc.get("kind") and doc.get("apiVersion"):
                out.append(DeployUnit(kind="k8s", name=str((doc.get("metadata") or {}).get("name", rel)), file=rel,
                                      details={"kind": str(doc["kind"])}))
        elif name == "persistence.xml":
            out.extend(_persistence_units(content, rel))
        elif name.startswith("application") and name.endswith((".properties", ".yml", ".yaml")):
            details = {}
            for key in ("spring.datasource.url", "server.port", "spring.profiles.active", "spring.jpa.database-platform"):
                m = re.search(rf"^{re.escape(key)}\s*[=:]\s*(.+)$", content, re.M)
                if m:
                    details[key] = m.group(1).strip()
            out.append(DeployUnit(kind="app-config", name=rel, file=rel, details=details))
        elif name in {"jenkinsfile", ".gitlab-ci.yml"} or "/.github/workflows/" in f"/{rel}":
            out.append(DeployUnit(kind="ci", name=rel, file=rel))
    return out


def _persistence_units(content: str, rel: str) -> list[DeployUnit]:
    try:
        root = ET.fromstring(content)
    except ET.ParseError:
        return [DeployUnit(kind="persistence-unit", name=rel, file=rel)]
    out = []
    for unit in root.iter():
        if unit.tag.endswith("persistence-unit"):
            details: dict = {}
            for prop in unit.iter():
                if prop.tag.endswith("property") and prop.get("name", "").endswith(("jdbc.url", "connection.url")):
                    details["jdbc_url"] = prop.get("value", "")
                if prop.tag.endswith("provider") and prop.text:
                    details["provider"] = prop.text.strip()
            out.append(DeployUnit(kind="persistence-unit", name=unit.get("name", rel), file=rel, details=details))
    return out or [DeployUnit(kind="persistence-unit", name=rel, file=rel)]


def build_units(files: list[tuple[Path, str]]) -> list[BuildUnit]:
    out: list[BuildUnit] = []
    for path, rel in files:
        name = path.name.lower()
        try:
            content = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if name == "pom.xml":
            try:
                root = ET.fromstring(content)
            except ET.ParseError:
                out.append(BuildUnit(tool="maven", file=rel))
                continue
            ns = root.tag.split("}")[0] + "}" if root.tag.startswith("{") else ""
            artifact = root.findtext(f"{ns}artifactId") or ""
            packaging = root.findtext(f"{ns}packaging") or "jar"
            deps = [d.findtext(f"{ns}artifactId") or "" for d in root.iter(f"{ns}dependency")]
            out.append(BuildUnit(tool="maven", file=rel, name=artifact, packaging=packaging, dependencies=[d for d in deps if d]))
        elif name.startswith("build.gradle"):
            deps = re.findall(r"""(?:implementation|api|compile|runtimeOnly)\s*\(?\s*['"]([^'"]+)['"]""", content)
            out.append(BuildUnit(tool="gradle", file=rel, dependencies=[d.split(":")[1] if ":" in d else d for d in deps]))
        elif name == "package.json":
            try:
                doc = json.loads(content)
            except json.JSONDecodeError:
                continue
            out.append(BuildUnit(tool="npm", file=rel, name=str(doc.get("name", "")),
                                 dependencies=sorted({**(doc.get("dependencies") or {}), **(doc.get("devDependencies") or {})})))
        elif name == "pyproject.toml":
            m = re.search(r'^name\s*=\s*"([^"]+)"', content, re.M)
            deps = re.findall(r'^\s*"([A-Za-z0-9_.\-]+)', content.split("dependencies", 1)[1], re.M) if "dependencies" in content else []
            out.append(BuildUnit(tool="python", file=rel, name=m.group(1) if m else "", dependencies=deps))
        elif name.startswith("requirements") and name.endswith(".txt"):
            deps = [re.split(r"[<>=!~\[; ]", l.strip(), 1)[0] for l in content.splitlines() if l.strip() and not l.startswith("#")]
            out.append(BuildUnit(tool="pip", file=rel, dependencies=[d for d in deps if d]))
        elif name in {"go.mod", "cargo.toml", "gemfile", "composer.json", "makefile", "cmakelists.txt", "setup.py", "build.xml"}:
            out.append(BuildUnit(tool=name, file=rel))
    return out


# ------------------------------------------------------------------- layers

def assign_layers(symbols: dict[str, Symbol], rules: dict) -> dict[str, list[str]]:
    alias_to_layer = {a.lower(): layer["id"] for layer in rules["layers"] for a in layer["aliases"]}
    by_layer: dict[str, set[str]] = defaultdict(set)
    for s in symbols.values():
        if s.is_test or s.kind == "module" and s.language == "java":
            continue
        segments = [p for p in (s.package.split(".") if s.package else [])] + s.file.split("/")[:-1]
        layer = next((alias_to_layer[seg.lower()] for seg in reversed(segments) if seg.lower() in alias_to_layer), None)
        s.layer = layer
        if layer:
            by_layer[layer].add(s.package or s.file.rsplit("/", 1)[0])
    order = [layer["id"] for layer in rules["layers"]]
    return {layer: sorted(by_layer[layer]) for layer in order if by_layer.get(layer)}


# ------------------------------------------------------------------ signals

def _import_hits(imports: list[str], markers: list[str]) -> list[str]:
    """An import matches a marker that equals it, prefixes it, or equals one of its dotted segments."""
    hits = []
    for imp in imports:
        segments = {seg.lower() for seg in imp.split(".")}
        for m in markers:
            ml = m.lower()
            if imp.lower() == ml or imp.lower().startswith(ml + ".") or ("." not in ml and ml in segments):
                hits.append(imp)
                break
    return hits


def _name_hits(named: list[tuple[str, str]], markers: list[str]) -> list[str]:
    """(owner, simple name) pairs whose name equals a marker's last segment exactly."""
    wanted = {m.rsplit(".", 1)[-1] for m in markers}
    return [f"{owner} {name}" for owner, name in named if name in wanted]


def derive_signals(card: RepositoryCard, imports: list[str], rules: dict, root: Path) -> dict[str, list[str]]:
    mk = rules["markers"]
    prod = [s for s in card.symbols.values() if not s.is_test]
    annotations = [(s.id, "@" + _ann(a).rsplit(".", 1)[-1]) for s in prod for a in s.annotations] + \
                  [(f"{s.id}.{m.name}", "@" + _ann(a).rsplit(".", 1)[-1]) for s in prod for m in s.methods for a in m.annotations]
    annotations = [(owner, name.lstrip("@")) for owner, name in annotations]
    supertypes = [(s.id, t.split("<", 1)[0].rsplit(".", 1)[-1]) for s in prod for t in s.extends + s.implements]

    def code_hits(markers: list[str], *, use_imports=True, use_annotations=True, use_supertypes=True) -> list[str]:
        return ((_import_hits(imports, markers) if use_imports else [])
                + (_name_hits(annotations, markers) if use_annotations else [])
                + (_name_hits(supertypes, markers) if use_supertypes else []))
    sig: dict[str, list[str]] = {}

    def add(name: str, evidence: list[str], limit: int = 5):
        if evidence:
            sig[name] = sorted(set(evidence))[:limit]

    add("rest-api", [f"{e.symbol}: {e.detail}" for e in card.entry_points if e.kind == "http-route"])
    add("gui-client", _import_hits(imports, mk["gui-client"]) + _name_hits(supertypes, mk["gui-supertypes"]))
    add("web-client", [f.path for f in card.files if f.file_class == "web"])
    covered = [s for s in prod if s.layer and s.kind != "module"]
    typed = [s for s in prod if s.kind != "module"]
    lr = rules["layered_rule"]
    if typed and len(card.layers) >= lr["min_layers"] and len(covered) / len(typed) >= lr["min_coverage"]:
        sig["layered"] = [f"{layer}: {', '.join(pk[:3])}" for layer, pk in card.layers.items()]
    internal_inh = [f"{e.source} {e.kind} {e.target}" for e in card.edges
                    if e.kind in {"extends", "implements"} and not card.symbols[e.source].is_test]
    if len(internal_inh) >= rules["min_inheritance_edges"]:
        add("inheritance", internal_inh)
    add("crosscutting", code_hits(mk["crosscutting"]))
    add("persisted-data", [f"{e.name} ({e.source}, {e.file})" for e in card.entities])
    add("event-bus", code_hits(mk["event-bus"]))
    add("data-flow", _import_hits(imports, mk["data-flow"]))
    add("threads", code_hits(mk["threads"]))
    add("variability", code_hits(mk["variability"], use_supertypes=False))
    app_services = [u for u in card.deploy if u.kind == "compose-service" and u.details.get("build")]
    services_markers = code_hits(mk["services"], use_supertypes=False)
    if len(app_services) >= 2 or services_markers:
        add("services", [f"compose service {u.name}" for u in app_services] + services_markers)
    store_deps = Counter(d for u in app_services for d in (u.details.get("depends_on") or []))
    shared = [f"{d} used by {n} services" for d, n in store_deps.items() if n >= 2]
    add("shared-repository", shared)
    compose = [u for u in card.deploy if u.kind == "compose-service"]
    if len(compose) >= 3 and app_services:
        add("multi-tier", [f"compose service {u.name}" for u in compose])
    lifecycle = []
    enum_ids = {s.id for s in prod if s.kind == "enum" and re.search(r"(status|state)$", s.name, re.I)}
    for e in card.edges:
        if e.kind == "field" and e.target in enum_ids:
            lifecycle.append(f"{e.source}.{e.detail} : {e.target}")
    for e in card.edges:
        if e.kind in {"extends", "implements"} and re.search(r"(status|state)$", e.target.rsplit(".", 1)[-1], re.I):
            lifecycle.append(f"{e.source} {e.kind} {e.target}")
    add("lifecycle", lifecycle)
    add("deploy-config", [f"{u.kind} {u.name}" for u in card.deploy if u.kind != "ci"])
    add("build-config", [f"{u.tool} {u.file}" for u in card.build])
    owners = [f.path for f in card.files if f.path.rsplit("/", 1)[-1] == "CODEOWNERS"]
    add("ownership", owners)
    import fnmatch
    adr = [f.path for f in card.files if f.file_class == "docs" and (
        any(fnmatch.fnmatch(f.path.rsplit("/", 1)[-1].lower(), p) for p in rules["decision_record_names"])
        or {p.lower() for p in f.path.split("/")[:-1]} & set(rules["decision_record_paths"]))]
    add("decision-records", adr)
    documents = {"pdf", "doc", "docx", "odt", "rtf"}
    req = [f.path for f in card.files if (f.file_class == "docs" or f.path.rsplit(".", 1)[-1].lower() in documents) and
           any(fnmatch.fnmatch(f.path.rsplit("/", 1)[-1].lower(), p) for p in rules["requirement_doc_names"])]
    add("requirement-docs", req)
    add("tests", [f.path for f in card.files if f.file_class == "test"])
    return sig


def gui_entry_points(card: RepositoryCard, rules: dict) -> list[EntryPoint]:
    supers = set(rules["markers"]["gui-supertypes"])
    out = []
    for s in card.symbols.values():
        if not s.is_test and any(t.split(".")[-1].split("<")[0] in supers for t in s.extends):
            out.append(EntryPoint(kind="gui", symbol=s.id, file=s.file, line=s.start_line, detail=s.extends[0]))
    return out
