"""c4plantuml, structurizr and graphviz renderers: real syntax checks plus checks the generic contract cannot make."""

import re
import shutil
import subprocess

import pytest

from task2view.phase7.notations import MODEL_KINDS, get_renderer

from .view_samples import SAMPLES


def _render(language, kind):
    return get_renderer(language).render(SAMPLES[kind]()).source


# ---------------------------------------------------------------- real syntax checks

@pytest.mark.skipif(shutil.which("plantuml") is None, reason="plantuml not installed")
@pytest.mark.parametrize("model_kind", MODEL_KINDS)
def test_c4plantuml_compiles(model_kind, tmp_path):
    src = tmp_path / "v.puml"
    src.write_text(_render("c4plantuml", model_kind))
    proc = subprocess.run(["plantuml", "-checkonly", str(src)], capture_output=True, text=True, timeout=120)
    assert proc.returncode == 0, proc.stdout + proc.stderr


@pytest.mark.skipif(shutil.which("dot") is None, reason="graphviz not installed")
@pytest.mark.parametrize("model_kind", MODEL_KINDS)
def test_graphviz_compiles(model_kind, tmp_path):
    src = tmp_path / "v.dot"
    src.write_text(_render("graphviz", model_kind))
    proc = subprocess.run(["dot", "-Tsvg", str(src), "-o", str(tmp_path / "v.svg")],
                          capture_output=True, text=True, timeout=120)
    assert proc.returncode == 0, proc.stderr
    assert "Warning" not in proc.stderr and "Error" not in proc.stderr, proc.stderr


# ---------------------------------------------------------------- structurizr well-formedness (no local CLI)

_STRING = re.compile(r'"(?:[^"\\]|\\.)*"')
_ASSIGN = re.compile(r"^\s*([A-Za-z_][\w-]*)\s*=\s*(person|softwareSystem|container|component|deploymentNode|"
                     r"infrastructureNode|containerInstance|softwareSystemInstance)\b")
_REL = re.compile(r"^\s*(?:\d+:\s*)?([A-Za-z_][\w-]*)\s*->\s*([A-Za-z_][\w-]*)")


def _structurizr_check(source: str):
    stripped = [_STRING.sub('""', line) for line in source.splitlines()]
    depth = 0
    for line in stripped:
        depth += line.count("{") - line.count("}")
        assert depth >= 0, f"unbalanced braces at: {line}"
    assert depth == 0, "unbalanced braces"
    assert stripped[0].lstrip().startswith("workspace")
    defined = {m.group(1) for line in stripped if (m := _ASSIGN.match(line))}
    for line in stripped:
        if m := _REL.match(line):
            assert m.group(1) in defined and m.group(2) in defined, f"undefined identifier in: {line}"
        if m := re.match(r"^\s*\w+\s*=\s*containerInstance\s+(\S+)", line):
            assert m.group(1) in defined, f"undefined container in: {line}"
    for line in stripped:
        if m := re.match(r"^\s*(component|dynamic)\s+(\S+)", line):
            assert m.group(2) in defined or m.group(2) == "*", f"undefined view scope in: {line}"
    assert "model {" in source and "views {" in source


@pytest.mark.parametrize("model_kind", MODEL_KINDS)
def test_structurizr_well_formed(model_kind):
    _structurizr_check(_render("structurizr", model_kind))


def test_structurizr_dynamic_steps_have_model_relationships():
    src = _render("structurizr", "uml-communication")
    model = src.split("views {")[0]
    dynamic = src.split("dynamic ")[1]
    for src_id, tgt_id in re.findall(r"^\s*(\w+) -> (\w+)", dynamic, re.M):
        assert re.search(rf"^\s*{src_id} -> {tgt_id} ", model, re.M), (src_id, tgt_id)
    assert "[alt order not NEW] rejected" in dynamic


# ---------------------------------------------------------------- semantic checks

def test_c4plantuml_uses_c4_stdlib_includes():
    for kind, include in {"uml-component": "C4_Component", "uml-sequence": "C4_Sequence",
                          "uml-communication": "C4_Dynamic", "uml-deployment": "C4_Deployment",
                          "uml-usecase": "C4_Context"}.items():
        src = _render("c4plantuml", kind)
        assert f"!include <C4/{include}>" in src
        assert "http" not in src  # offline stdlib only


def test_c4plantuml_nesting_and_responsibilities():
    src = _render("c4plantuml", "uml-component")
    assert re.search(r'Boundary\(e_group_layer_application_663bcf, "Application".*\{\n\s+Component\(e_cmp_svc_OrderService_51653a',
                     src)
    assert "charges the gateway" in src.split("Component(e_cmp_svc_OrderService_51653a")[1].split("\n")[0]
    dep = _render("c4plantuml", "uml-deployment")
    assert re.search(r'Deployment_Node\(e_node_shop_e761f6, "shop".*\{\n\s+Container\(e_artifact_shop_service_b1b9fa', dep)
    assert "ContainerDb(e_datastore_db_6aa6dd" in dep


def test_c4plantuml_sequence_order_and_fragment():
    src = _render("c4plantuml", "uml-sequence")
    assert src.index("1. POST") < src.index("2. pay(id)") < src.index("3. rejected") < src.index("4. order")
    assert "alt order not NEW" in src and "\nend\n" in src
    comm = _render("c4plantuml", "uml-communication")
    assert 'RelIndex(3, e_cmp_svc_OrderService_51653a, e_cmp_web_OrderController_5b247b, "[order not NEW] rejected")' in comm


def test_c4plantuml_class_and_usecase_relations():
    cls = _render("c4plantuml", "uml-class")
    assert 'e_ent_Order_67759b "*" --> "1" e_ent_Customer_c28521' in cls
    assert "e_ent_VipCustomer_73dffd --|> e_ent_Customer_c28521" in cls
    uc = _render("c4plantuml", "uml-usecase")
    assert "e_uc_pay_0c69bc ..> e_uc_login_1d9e51 : <<include>>" in uc
    assert re.search(r'System_Boundary\(e_group_system_e867ad, "Shop"\) \{\n\s+usecase "Pay order"', uc)


def test_structurizr_constructs():
    comp = _render("structurizr", "uml-component")
    assert re.search(r'group "Application" \{\n\s+e_cmp_svc_OrderService_51653a = component "OrderService" "[^"]*charges the gateway',
                     comp)
    assert "component app " in comp
    dep = _render("structurizr", "uml-deployment")
    assert re.search(r'deploymentNode "shop".*\{\n\s+i_e_artifact_shop_service_b1b9fa = containerInstance', dep)
    assert 'deployment * "Default"' in dep
    cls = _render("structurizr", "uml-class")
    assert '"customer [*..1]"' in cls and "Generalization" in cls
    uc = _render("structurizr", "uml-usecase")
    assert '"«include»"' in uc
    table = _render("structurizr", "table")
    assert '"Files" "docs/adr/adr-001.md"' in table


def test_graphviz_constructs():
    comp = _render("graphviz", "uml-component")
    cluster = comp.split("subgraph cluster_e_group_layer_application_663bcf {")[1].split("}")[0]
    assert "e_cmp_svc_OrderService_51653a" in cluster and "charges the gateway" in cluster
    cls = _render("graphviz", "uml-class")
    assert 'taillabel="*", headlabel="1"' in cls and 'arrowhead="onormal"' in cls
    seq = _render("graphviz", "uml-sequence")
    labels = re.findall(r'label="(?:\[[^\]]*\] )?(\d+)\. ', seq)
    assert labels == ["1", "2", "3", "4"]
    assert "[alt order not NEW] 3. rejected" in seq
    act = _render("graphviz", "uml-activity")
    assert 'shape="diamond", label="order not NEW"' in act
    uc = _render("graphviz", "uml-usecase")
    assert 'label="«include»"' in uc and "subgraph cluster_e_group_system_e867ad" in uc
    table = _render("graphviz", "table")
    assert "<TABLE" in table and "docs/adr/adr-001.md" in table
