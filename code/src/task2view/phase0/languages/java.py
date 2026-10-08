"""Java extractor (tree-sitter-java).

Declares: types (class / interface / enum / record / annotation, nested types as
Outer.Inner), fields, methods, annotations, enum constants.
References: imports, extends, implements, field / parameter / return types,
instantiation, and method calls whose receiver type is known from a field,
parameter, local variable, or a static type name. Strings and comments are
never read, so a name in a log message does not create an edge.
"""

from __future__ import annotations

import tree_sitter as ts
import tree_sitter_java as tsjava

from task2view.contracts.card import Field_, Method, Symbol
from task2view.phase0.languages.base import FileUnit, Import, LanguageExtractor, RawEntry, RawRef, text, walk

_LANG = ts.Language(tsjava.language())
_TYPE_DECLS = {
    "class_declaration": "class",
    "interface_declaration": "interface",
    "enum_declaration": "enum",
    "record_declaration": "record",
    "annotation_type_declaration": "annotation",
}
_ROUTE_ANNOTATIONS = {"RequestMapping", "GetMapping", "PostMapping", "PutMapping", "DeleteMapping", "PatchMapping",
                      "GET", "POST", "PUT", "DELETE", "PATCH", "Path"}
_LISTENER_ANNOTATIONS = {"EventListener", "KafkaListener", "RabbitListener", "JmsListener", "Subscribe"}


def _annotations(node, src: bytes) -> list[str]:
    out = []
    for child in node.children:
        if child.type == "modifiers":
            for mod in child.children:
                if mod.type in {"marker_annotation", "annotation"}:
                    name = mod.child_by_field_name("name")
                    args = mod.child_by_field_name("arguments")
                    label = text(name, src).split(".")[-1] if name else text(mod, src).lstrip("@")
                    out.append(label + (text(args, src) if args else ""))
    return out


def _ann_name(annotation: str) -> str:
    return annotation.split("(", 1)[0]


def _type_names(node, src: bytes) -> list[str]:
    """Every type identifier inside a type node (List<Reservation> -> List, Reservation)."""
    if node is None:
        return []
    names = []
    for n in walk(node):
        if n.type == "scoped_type_identifier":
            names.append(text(n, src))
        elif n.type == "type_identifier" and (n.parent is None or n.parent.type != "scoped_type_identifier"):
            names.append(text(n, src))
    return names


class JavaExtractor(LanguageExtractor):
    language = "java"

    def __init__(self):
        self._parser = ts.Parser(_LANG)

    def extract(self, path: str, source: bytes, *, is_test: bool) -> FileUnit:
        tree = self._parser.parse(source)
        unit = FileUnit(path=path, language="java")
        root = tree.root_node
        for child in root.children:
            if child.type == "package_declaration":
                for n in child.children:
                    if n.type in {"scoped_identifier", "identifier"}:
                        unit.package = text(n, source)
            elif child.type == "import_declaration":
                wildcard = any(n.type == "asterisk" for n in child.children)
                name = next((text(n, source) for n in child.children if n.type in {"scoped_identifier", "identifier"}), "")
                if name:
                    unit.imports.append(Import(name=name, line=child.start_point[0] + 1, wildcard=wildcard))
        for child in root.children:
            if child.type in _TYPE_DECLS:
                self._type(child, source, unit, outer=None, is_test=is_test)
        return unit

    def _type(self, node, src: bytes, unit: FileUnit, *, outer: str | None, is_test: bool) -> None:
        name_node = node.child_by_field_name("name")
        if name_node is None:
            return
        name = text(name_node, src)
        prefix = outer or unit.package
        sid = f"{prefix}.{name}" if prefix else name
        symbol = Symbol(
            id=sid, name=name, kind=_TYPE_DECLS[node.type], file=unit.path,
            start_line=node.start_point[0] + 1, end_line=node.end_point[0] + 1,
            language="java", package=unit.package, is_test=is_test,
            annotations=_annotations(node, src),
        )
        superclass = node.child_by_field_name("superclass")
        for t in _type_names(superclass, src)[:1]:
            symbol.extends.append(t)
            unit.refs.append(RawRef(sid, t, "extends", superclass.start_point[0] + 1))
        for child in node.children:
            if child.type in {"super_interfaces", "extends_interfaces"}:
                for t in _type_names(child, src):
                    if node.type == "interface_declaration":
                        symbol.extends.append(t)
                        unit.refs.append(RawRef(sid, t, "extends", child.start_point[0] + 1))
                    else:
                        symbol.implements.append(t)
                        unit.refs.append(RawRef(sid, t, "implements", child.start_point[0] + 1))
        for ann in symbol.annotations:
            unit.refs.append(RawRef(sid, _ann_name(ann), "annotated", node.start_point[0] + 1))
        unit.symbols.append(symbol)

        if node.type == "record_declaration":
            params = node.child_by_field_name("parameters")
            for p in (params.children if params else []):
                if p.type == "formal_parameter":
                    self._field_from(p, src, symbol, unit)

        body = node.child_by_field_name("body")
        if body is None:
            return
        field_types: dict[str, str] = {}
        members = list(body.children)
        for child in body.children:
            if child.type == "enum_body_declarations":
                members.extend(child.children)
            if child.type == "enum_constant":
                cname = child.child_by_field_name("name")
                if cname:
                    symbol.enum_constants.append(text(cname, src))
        for member in members:
            if member.type == "field_declaration":
                for fld in self._fields(member, src, symbol, unit):
                    if fld.type:
                        field_types[fld.name] = fld.type
        for member in members:
            if member.type in _TYPE_DECLS:
                self._type(member, src, unit, outer=sid, is_test=is_test)
            elif member.type in {"method_declaration", "constructor_declaration"}:
                self._method(member, src, symbol, unit, field_types)

    def _fields(self, node, src: bytes, symbol: Symbol, unit: FileUnit) -> list[Field_]:
        type_node = node.child_by_field_name("type")
        type_text = text(type_node, src) if type_node else None
        anns = _annotations(node, src)
        is_static = any(c.type == "modifiers" and "static" in text(c, src).split() for c in node.children)
        out = []
        for child in node.children:
            if child.type == "variable_declarator":
                name = child.child_by_field_name("name")
                if name is None:
                    continue
                fld = Field_(name=text(name, src), type=type_text, annotations=anns, static=is_static,
                             line=node.start_point[0] + 1)
                symbol.fields.append(fld)
                out.append(fld)
                for t in _type_names(type_node, src):
                    unit.refs.append(RawRef(symbol.id, t, "field", fld.line, fld.name))
        return out

    def _field_from(self, param, src: bytes, symbol: Symbol, unit: FileUnit) -> None:
        type_node = param.child_by_field_name("type")
        name = param.child_by_field_name("name")
        if name is None:
            return
        fld = Field_(name=text(name, src), type=text(type_node, src) if type_node else None, line=param.start_point[0] + 1)
        symbol.fields.append(fld)
        for t in _type_names(type_node, src):
            unit.refs.append(RawRef(symbol.id, t, "field", fld.line, fld.name))

    def _method(self, node, src: bytes, symbol: Symbol, unit: FileUnit, field_types: dict[str, str]) -> None:
        name_node = node.child_by_field_name("name")
        name = text(name_node, src) if name_node else "<init>"
        anns = _annotations(node, src)
        method = Method(name=name, start_line=node.start_point[0] + 1, end_line=node.end_point[0] + 1, annotations=anns)
        local_types: dict[str, str] = dict(field_types)
        params = node.child_by_field_name("parameters")
        for p in (params.children if params else []):
            if p.type in {"formal_parameter", "spread_parameter"}:
                t = p.child_by_field_name("type")
                n = p.child_by_field_name("name")
                if t is not None:
                    method.params.append(text(t, src))
                    for tn in _type_names(t, src):
                        unit.refs.append(RawRef(symbol.id, tn, "param", p.start_point[0] + 1, name))
                    if n is not None:
                        local_types[text(n, src)] = text(t, src)
        returns = node.child_by_field_name("type")
        if returns is not None:
            method.returns = text(returns, src)
            for tn in _type_names(returns, src):
                unit.refs.append(RawRef(symbol.id, tn, "returns", node.start_point[0] + 1, name))
        body = node.child_by_field_name("body")
        if body is not None:
            self._body(body, src, symbol, unit, method, local_types)
        symbol.methods.append(method)
        self._entry(anns, symbol, method, unit, node)

    def _body(self, body, src: bytes, symbol: Symbol, unit: FileUnit, method: Method, local_types: dict[str, str]) -> None:
        for n in walk(body):
            if n.type in {"local_variable_declaration", "enhanced_for_statement", "catch_formal_parameter", "resource"}:
                t = n.child_by_field_name("type")
                if t is None:
                    continue
                type_text = text(t, src)
                for child in n.children:
                    if child.type == "variable_declarator":
                        vn = child.child_by_field_name("name")
                        if vn is not None:
                            local_types[text(vn, src)] = type_text
                vn = n.child_by_field_name("name")
                if vn is not None:
                    local_types[text(vn, src)] = type_text
            elif n.type == "object_creation_expression":
                t = n.child_by_field_name("type")
                for tn in _type_names(t, src)[:1]:
                    unit.refs.append(RawRef(symbol.id, tn, "instantiates", n.start_point[0] + 1, method.name))
            elif n.type == "method_invocation":
                obj = n.child_by_field_name("object")
                mname = n.child_by_field_name("name")
                if obj is None or mname is None:
                    continue
                receiver = text(obj, src)
                if receiver.startswith("this."):
                    receiver = receiver[5:]
                receiver_type = local_types.get(receiver)
                if receiver_type is None and receiver[:1].isupper() and receiver.replace(".", "").isalnum():
                    receiver_type = receiver  # static call on a type name
                if receiver_type is not None:
                    base = _type_names_from_text(receiver_type)
                    if base:
                        target = f"{base}.{text(mname, src)}"
                        unit.refs.append(RawRef(symbol.id, target, "calls", n.start_point[0] + 1, method.name))
                        method.calls.append(target)

    def _entry(self, anns: list[str], symbol: Symbol, method: Method, unit: FileUnit, node) -> None:
        line = node.start_point[0] + 1
        names = {_ann_name(a) for a in anns}
        if method.name == "main" and any(p.startswith("String") for p in method.params):
            unit.entries.append(RawEntry("main", symbol.id, line, "main"))
        class_route = next((a for a in symbol.annotations if _ann_name(a) in {"RequestMapping", "Path"}), "")
        for a in anns:
            if _ann_name(a) in _ROUTE_ANNOTATIONS:
                unit.entries.append(RawEntry("http-route", symbol.id, line, f"{_ann_name(a)} {class_route} {a} {method.name}".strip()))
        if "Scheduled" in names:
            unit.entries.append(RawEntry("scheduled", symbol.id, line, method.name))
        if names & _LISTENER_ANNOTATIONS:
            unit.entries.append(RawEntry("listener", symbol.id, line, method.name))


def _type_names_from_text(type_text: str) -> str:
    """Base type of a declared type: 'List<Reservation>' -> 'List', 'a.b.Type' -> 'a.b.Type'."""
    return type_text.split("<", 1)[0].replace("[]", "").strip()
