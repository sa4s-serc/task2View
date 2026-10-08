"""Mermaid, D2 and nomnoml renderers: real Mermaid compile (mmdc) and structural checks for D2 / nomnoml."""

import re
import shutil
import subprocess

import pytest

from task2view.contracts.views import (
    ArchitectureView, Interaction, ViewAttribute, ViewElement, ViewFragment, ViewRelation,
)
from task2view.phase7.notations import MODEL_KINDS, get_renderer

from .view_samples import SAMPLES


def stress_view(model_kind: str) -> ArchitectureView:
    """Deep nesting, cross-container edges, odd characters, a loop fragment and an idle participant."""
    return ArchitectureView(
        id="V-stress", viewpoint_id="stress", viewpoint_name="Stress", vb_ref="test", model_kind=model_kind,
        title="Stress: a <b> #1; [x]", purpose="test", detail_level="feature", max_elements=20,
        elements=[
            ViewElement(id="group:outer", kind="layer", name="Outer layer", group=True),
            ViewElement(id="group:inner", kind="module", name="Inner", group=True, parent="group:outer"),
            ViewElement(id="cmp:a", kind="component", name="Alpha", parent="group:inner",
                        responsibilities=["handles <input> #1; fast", 'quotes "x"']),
            ViewElement(id="cmp:b", kind="class", name="Beta", parent="group:outer", stereotype="service",
                        attributes=[ViewAttribute(name="id", type="int", key=True)], responsibilities=["does b"]),
            ViewElement(id="cmp:c", kind="interface", name="Gamma"),
            ViewElement(id="actor:u", kind="actor", name="User"),
            ViewElement(id="cmp:idle", kind="component", name="Idle"),
        ],
        relations=[
            ViewRelation(id="r1", kind="uses", source="cmp:a", target="cmp:b", label="call: now"),
            ViewRelation(id="r2", kind="implements", source="cmp:b", target="cmp:c"),
            ViewRelation(id="r3", kind="association", source="actor:u", target="cmp:a", multiplicity="1..*"),
            ViewRelation(id="r4", kind="composition", source="cmp:c", target="cmp:a"),
        ],
        interactions=[
            Interaction(order=1, source="actor:u", target="cmp:a", message="go(x; y)"),
            Interaction(order=2, source="cmp:a", target="cmp:b", message="poll #2", fragment="f1"),
            Interaction(order=3, source="cmp:b", target="cmp:a", message="ok", kind="return", fragment="f1"),
            Interaction(order=4, source="cmp:a", target="actor:u", message="done", kind="return"),
        ],
        fragments=[ViewFragment(id="f1", kind="loop", guard="until ready")],
    )


CASES = [(k, SAMPLES[k]) for k in MODEL_KINDS] + [(f"stress-{k}", (lambda k=k: stress_view(k))) for k in MODEL_KINDS]
CASE_IDS = [c[0] for c in CASES]


# ------------------------------------------------------------------ mermaid: real compile
_ENV_ERRORS = ("Failed to launch the browser", "Could not find Chrome", "Could not find Chromium",
               "No usable sandbox", "libnss", "ECONNREFUSED", "Browser was not found", "spawn")


@pytest.mark.skipif(shutil.which("mmdc") is None, reason="mermaid-cli (mmdc) not installed")
@pytest.mark.parametrize("case,make", CASES, ids=CASE_IDS)
def test_mermaid_output_compiles(case, make, tmp_path):
    src, out = tmp_path / "in.mmd", tmp_path / "out.svg"
    src.write_text(get_renderer("mermaid").render(make()).source)
    proc = subprocess.run(["mmdc", "-q", "-i", str(src), "-o", str(out)], capture_output=True, text=True, timeout=180)
    log = proc.stdout + proc.stderr
    if proc.returncode != 0 and "Parse error" not in log and any(m in log for m in _ENV_ERRORS):
        pytest.skip(f"mmdc cannot run in this environment: {log.strip()[:200]}")
    assert proc.returncode == 0, src.read_text() + "\n" + log
    assert out.exists() and "<svg" in out.read_text()


@pytest.mark.parametrize("kind,keyword", [("uml-sequence", "sequenceDiagram"), ("uml-class", "classDiagram"),
                                          ("uml-state", "stateDiagram-v2"), ("uml-activity", "flowchart"),
                                          ("uml-component", "flowchart"), ("table", "flowchart")])
def test_mermaid_uses_expected_diagram_type(kind, keyword):
    source = get_renderer("mermaid").render(SAMPLES[kind]()).source
    assert keyword in source.splitlines()[3]


def test_mermaid_native_constructs():
    r = get_renderer("mermaid")
    seq = r.render(SAMPLES["uml-sequence"]()).source
    assert "alt order not NEW" in seq and "actor e_actor_customer_a992bb" in seq and "-->>" in seq
    cls = r.render(SAMPLES["uml-class"]()).source
    assert '"*" --> "1"' in cls and "<|--" in cls and "PK" in cls
    comp = r.render(SAMPLES["uml-component"]()).source
    assert 'subgraph e_group_layer_presentation_8df40c["Presentation"]' in comp
    uc = r.render(SAMPLES["uml-usecase"]()).source
    assert "«include»" in uc and "-.->" in uc
    assert "namespace" in r.render(stress_view("uml-class")).source
    assert "repeat" in r.render(stress_view("uml-activity")).source


# ------------------------------------------------------------------ d2: structural well-formedness
_STRING = re.compile(r'"(?:\\.|[^"\\])*"')
_ARROW = re.compile(r"\s(<->|->|<-|--)\s")


def _d2_structure(source: str):
    """Return (declared paths, [(scope, endpoint)]) and assert braces balance outside strings."""
    declared, edges, stack = set(), [], []  # stack entries: key path element, or None for attribute blocks
    in_block = False
    for raw in source.splitlines():
        if in_block:
            in_block = not raw.strip().startswith("`|")
            continue
        line = _STRING.sub('STR', raw)
        assert '"' not in line, f"unterminated string: {raw}"
        if line.rstrip().endswith("|`md"):
            in_block = True
        scope = [s for s in stack if s is not None]
        inside_attrs = any(s is None for s in stack)
        m_edge = _ARROW.search(line)
        if m_edge and not inside_attrs:
            left = line[:m_edge.start()].strip()
            right = re.split(r"[:{]", line[m_edge.end():], maxsplit=1)[0].strip()
            edges += [(tuple(scope), left), (tuple(scope), right)]
        elif not inside_attrs:
            m = re.match(r"\s*([A-Za-z_][\w.\-]*)\s*[:{]", line)
            if m:
                declared.add(".".join([*scope, m.group(1)]))
        for ch in line:
            if ch == "{":
                key = None
                if not m_edge and not inside_attrs and line.count("{") == 1 and line.rstrip().endswith("{"):
                    m = re.match(r"\s*([A-Za-z_][\w\-]*)\s*:", line)
                    key = m.group(1) if m and m.group(1) not in {"style", "source-arrowhead",
                                                                 "target-arrowhead"} else None
                stack.append(key)
            elif ch == "}":
                assert stack, f"unbalanced '}}' at: {raw}"
                stack.pop()
    assert not stack, "unbalanced '{'"
    assert not in_block, "unterminated block string"
    return declared, edges


@pytest.mark.parametrize("case,make", CASES, ids=CASE_IDS)
def test_d2_well_formed(case, make):
    view = make()
    source = get_renderer("d2").render(view).source
    declared, edges = _d2_structure(source)
    for scope, endpoint in edges:
        candidates = [".".join([*scope[:i], endpoint]) for i in range(len(scope), -1, -1)]
        assert any(c in declared for c in candidates), f"undeclared edge endpoint {endpoint!r} in {scope}\n{source}"
    for e in view.content_elements():
        assert e.name.replace('"', "'") in source


def test_d2_native_constructs():
    r = get_renderer("d2")
    seq = r.render(SAMPLES["uml-sequence"]()).source
    assert "shape: sequence_diagram" in seq and "shape: person" in seq and '"alt [order not NEW]"' in seq
    assert seq.index('"1. ') < seq.index('"2. ') < seq.index('"3. ') < seq.index('"4. ')
    cls = r.render(SAMPLES["uml-class"]()).source
    assert "shape: sql_table" in cls and "primary_key" in cls and "foreign_key" in cls
    assert 'source-arrowhead.label: "*"' in cls and "target-arrowhead.shape: triangle" in cls
    comp = r.render(SAMPLES["uml-component"]()).source
    assert "shape: cylinder" in comp
    assert "e_group_layer_presentation_8df40c.e_cmp_web_OrderController_5b247b -> e_group_layer_application_663bcf." in comp
    dep = r.render(SAMPLES["uml-deployment"]()).source
    assert "e_node_shop_e761f6.e_artifact_shop_service_b1b9fa" in dep
    assert "shape: class" in r.render(stress_view("uml-class")).source


def test_d2_responsibilities_not_on_edges():
    source = get_renderer("d2").render(SAMPLES["uml-component"]()).source
    for line in source.splitlines():
        if "->" in line:
            assert "charges the gateway" not in line and "accepts payment" not in line


# ------------------------------------------------------------------ nomnoml: structural well-formedness
def _classifiers(text: str):
    """Top-level [ ... ] spans of a scope, with the text between them."""
    out, depth, start = [], 0, None
    for i, ch in enumerate(text):
        if ch == "[":
            if depth == 0:
                start = i
            depth += 1
        elif ch == "]":
            depth -= 1
            assert depth >= 0, "unbalanced ']'"
            if depth == 0:
                out.append((start, i))
    assert depth == 0, "unbalanced '['"
    return out


def _split_top(text: str, sep: str):
    parts, depth, cur = [], 0, ""
    for ch in text:
        depth += ch == "["
        depth -= ch == "]"
        if ch in sep and depth == 0:
            parts.append(cur)
            cur = ""
        else:
            cur += ch
    return parts + [cur]


def _name(classifier: str) -> str:
    inner = classifier[1:-1].strip()
    inner = re.sub(r"^<[^>]*>\s*", "", inner)
    return _split_top(inner, "|")[0].strip()


def _check_nomnoml_scope(text: str, where: str):
    declared, used = set(), []
    for statement in _split_top(text, "\n;"):
        if not statement.strip() or statement.strip().startswith("#"):
            continue
        spans = _classifiers(statement)
        assert spans, f"statement without classifier in {where}: {statement!r}"
        if len(spans) == 1:
            cls = statement[spans[0][0]:spans[0][1] + 1]
            declared.add(_name(cls))
            inner = re.sub(r"^<[^>]*>\s*", "", cls[1:-1].strip())
            for compartment in _split_top(inner, "|")[1:]:
                if "[" in compartment:
                    _check_nomnoml_scope(compartment, _name(cls))
        else:
            assert len(spans) == 2, f"one edge per statement expected: {statement!r}"
            between = statement[spans[0][1] + 1:spans[1][0]]
            assert re.search(r"(-:>|--:>|\+->|o->|-->|->|--|-)", between), f"no arrow in {statement!r}"
            assert "[" not in between and "]" not in between
            used += [_name(statement[a:b + 1]) for a, b in spans]
    for name in used:
        assert name in declared, f"edge endpoint [{name}] not declared in scope {where}"


@pytest.mark.parametrize("case,make", CASES, ids=CASE_IDS)
def test_nomnoml_well_formed(case, make):
    view = make()
    source = get_renderer("nomnoml").render(view).source
    _classifiers(source)  # brackets balance
    if view.model_kind != "uml-activity":  # activity declares its nodes inline in the edges
        _check_nomnoml_scope(source, "top")


def test_nomnoml_native_constructs():
    r = get_renderer("nomnoml")
    pkg = r.render(SAMPLES["uml-package"]()).source
    assert "[<package> web|" in pkg and "[A|- does a]" in pkg
    cls = r.render(SAMPLES["uml-class"]()).source
    assert "[<class> Order|id: Long {PK};customer_id: Long {FK}" in cls
    assert "-:>" in cls and "* -> 1 customer" in cls
    uc = r.render(SAMPLES["uml-usecase"]()).source
    assert "[<actor> Customer]" in uc and "[<usecase> Pay order]" in uc and "«include»" in uc
    seq = r.render(SAMPLES["uml-sequence"]()).source
    assert seq.index("1. ") < seq.index("2. ") < seq.index("3. alt") < seq.index("4. ")
    assert "[<table>" in r.render(SAMPLES["table"]()).source
    stress = r.render(stress_view("uml-component")).source
    assert "Alpha → Beta" in stress  # cross-container edge keeps its real endpoints
