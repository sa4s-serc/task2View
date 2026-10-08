"""Python extractor (tree-sitter-python).

Declares: one module symbol per file, classes (with bases, class-level annotated
attributes as fields, methods), and top-level functions.
References: imports, base classes, calls to imported or local names, calls
through ``module.attr`` and ``Class.method``, and instantiation of local classes.
Entry points: ``if __name__ == "__main__"``, route decorators, CLI decorators.
"""

from __future__ import annotations

import tree_sitter as ts
import tree_sitter_python as tspy

from task2view.contracts.card import Field_, Method, Symbol
from task2view.phase0.languages.base import FileUnit, Import, LanguageExtractor, RawEntry, RawRef, text, walk

_LANG = ts.Language(tspy.language())
_ROUTE_DECORATORS = {"route", "get", "post", "put", "delete", "patch", "api_view", "websocket"}
_CLI_DECORATORS = {"command", "group", "callback"}


def module_id(path: str) -> str:
    parts = path[:-3].split("/") if path.endswith(".py") else path.split("/")
    if parts and parts[0] in {"src", "lib"} and len(parts) > 1:
        parts = parts[1:]
    if parts and parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(p for p in parts if p) or path


class PythonExtractor(LanguageExtractor):
    language = "python"

    def __init__(self):
        self._parser = ts.Parser(_LANG)

    def extract(self, path: str, source: bytes, *, is_test: bool) -> FileUnit:
        tree = self._parser.parse(source)
        root = tree.root_node
        mid = module_id(path)
        package = mid.rsplit(".", 1)[0] if "." in mid else ""
        unit = FileUnit(path=path, language="python", package=package, module_id=mid)
        module = Symbol(id=mid, name=mid.rsplit(".", 1)[-1], kind="module", file=path, start_line=1,
                        end_line=root.end_point[0] + 1, language="python", package=package, is_test=is_test)
        unit.symbols.append(module)
        local_names: dict[str, str] = {}  # bound name -> raw target (import or local def)

        for n in walk(root):
            if n.type == "import_statement":
                for child in n.children:
                    if child.type == "dotted_name":
                        name = text(child, source)
                        unit.imports.append(Import(name, n.start_point[0] + 1))
                        local_names[name.split(".")[0]] = name.split(".")[0]
                        unit.refs.append(RawRef(mid, name, "imports", n.start_point[0] + 1))
                    elif child.type == "aliased_import":
                        name = text(child.child_by_field_name("name"), source)
                        alias = text(child.child_by_field_name("alias"), source)
                        unit.imports.append(Import(name, n.start_point[0] + 1, alias=alias))
                        local_names[alias] = name
                        unit.refs.append(RawRef(mid, name, "imports", n.start_point[0] + 1))
            elif n.type == "import_from_statement":
                mod_node = n.child_by_field_name("module_name")
                mod = _resolve_relative(text(mod_node, source), package, path) if mod_node else ""
                names = [c for c in n.children if c.type in {"dotted_name", "aliased_import"} and c != mod_node]
                if any(c.type == "wildcard_import" for c in n.children):
                    unit.imports.append(Import(mod, n.start_point[0] + 1, wildcard=True))
                    unit.refs.append(RawRef(mid, mod, "imports", n.start_point[0] + 1))
                for c in names:
                    if c.type == "aliased_import":
                        name, alias = text(c.child_by_field_name("name"), source), text(c.child_by_field_name("alias"), source)
                    else:
                        name = alias = text(c, source)
                    full = f"{mod}.{name}" if mod else name
                    unit.imports.append(Import(full, n.start_point[0] + 1, alias=alias))
                    local_names[alias] = full
                    unit.refs.append(RawRef(mid, full, "imports", n.start_point[0] + 1))

        for child in root.children:
            node, decorators = _undecorate(child, source)
            if node.type == "class_definition":
                self._class(node, decorators, source, unit, mid, local_names, is_test)
            elif node.type == "function_definition":
                fname = text(node.child_by_field_name("name"), source)
                local_names.setdefault(fname, f"{mid}.{fname}")
                fn = Symbol(id=f"{mid}.{fname}", name=fname, kind="function", file=path,
                            start_line=node.start_point[0] + 1, end_line=node.end_point[0] + 1,
                            language="python", package=mid, is_test=is_test, annotations=decorators)
                unit.symbols.append(fn)
                method = Method(name=fname, start_line=fn.start_line, end_line=fn.end_line, annotations=decorators)
                self._calls(node, source, unit, fn.id, method, local_names)
                fn.methods.append(method)
                self._entries(decorators, fn.id, fn.start_line, unit)
            elif node.type == "if_statement" and "__name__" in text(node.child_by_field_name("condition"), source):
                unit.entries.append(RawEntry("main", mid, node.start_point[0] + 1, "__main__"))
                self._calls(node, source, unit, mid, None, local_names)
        return unit

    def _class(self, node, decorators, src: bytes, unit: FileUnit, mid: str, local_names, is_test: bool) -> None:
        name = text(node.child_by_field_name("name"), src)
        sid = f"{mid}.{name}"
        local_names.setdefault(name, sid)
        symbol = Symbol(id=sid, name=name, kind="class", file=unit.path, start_line=node.start_point[0] + 1,
                        end_line=node.end_point[0] + 1, language="python", package=mid, is_test=is_test,
                        annotations=decorators)
        bases = node.child_by_field_name("superclasses")
        for b in (bases.children if bases else []):
            if b.type in {"identifier", "attribute"}:
                base = text(b, src)
                symbol.extends.append(base)
                unit.refs.append(RawRef(sid, local_names.get(base.split(".")[0], base.split(".")[0]) + _tail(base),
                                        "extends", b.start_point[0] + 1))
        unit.symbols.append(symbol)
        body = node.child_by_field_name("body")
        for stmt in (body.children if body else []):
            inner, decs = _undecorate(stmt, src)
            if inner.type == "function_definition":
                mname = text(inner.child_by_field_name("name"), src)
                method = Method(name=mname, start_line=inner.start_point[0] + 1, end_line=inner.end_point[0] + 1,
                                annotations=decs)
                self._calls(inner, src, unit, sid, method, local_names)
                symbol.methods.append(method)
                self._entries(decs, sid, method.start_line, unit)
            elif inner.type == "expression_statement":
                for a in inner.children:
                    if a.type == "assignment":
                        left = a.child_by_field_name("left")
                        type_node = a.child_by_field_name("type")
                        right = a.child_by_field_name("right")
                        if left is not None and left.type == "identifier":
                            ftype = text(type_node, src) if type_node is not None else (
                                text(right.child_by_field_name("function"), src) if right is not None and right.type == "call" else None)
                            symbol.fields.append(Field_(name=text(left, src), type=ftype, line=a.start_point[0] + 1))
                            if type_node is not None:
                                for ident in walk(type_node):
                                    if ident.type == "identifier":
                                        tn = text(ident, src)
                                        unit.refs.append(RawRef(sid, local_names.get(tn, tn), "field", a.start_point[0] + 1, text(left, src)))

    def _calls(self, node, src: bytes, unit: FileUnit, source_id: str, method: Method | None, local_names) -> None:
        for n in walk(node):
            if n.type != "call":
                continue
            fn = n.child_by_field_name("function")
            if fn is None:
                continue
            line = n.start_point[0] + 1
            detail = method.name if method else ""
            if fn.type == "identifier":
                name = text(fn, src)
                if name in local_names:
                    target = local_names[name]
                    kind = "instantiates" if name[:1].isupper() else "calls"
                    unit.refs.append(RawRef(source_id, target, kind, line, detail))
                    if method is not None:
                        method.calls.append(target)
            elif fn.type == "attribute":
                obj = fn.child_by_field_name("object")
                attr = fn.child_by_field_name("attribute")
                if obj is not None and obj.type == "identifier" and attr is not None:
                    head = text(obj, src)
                    if head in local_names:
                        target = f"{local_names[head]}.{text(attr, src)}"
                        unit.refs.append(RawRef(source_id, target, "calls", line, detail))
                        if method is not None:
                            method.calls.append(target)

    def _entries(self, decorators: list[str], sid: str, line: int, unit: FileUnit) -> None:
        for d in decorators:
            head = d.split("(", 1)[0]
            last = head.rsplit(".", 1)[-1]
            if last in _ROUTE_DECORATORS and "." in head:
                unit.entries.append(RawEntry("http-route", sid, line, d))
            elif last in _CLI_DECORATORS and "." in head:
                unit.entries.append(RawEntry("cli", sid, line, d))


def _undecorate(node, src: bytes):
    if node.type != "decorated_definition":
        return node, []
    decorators = [text(c, src).lstrip("@").strip() for c in node.children if c.type == "decorator"]
    inner = node.child_by_field_name("definition")
    return (inner if inner is not None else node), decorators


def _tail(dotted: str) -> str:
    return "." + dotted.split(".", 1)[1] if "." in dotted else ""


def _resolve_relative(mod: str, package: str, path: str) -> str:
    if not mod.startswith("."):
        return mod
    dots = len(mod) - len(mod.lstrip("."))
    base = package.split(".") if package else []
    if path.endswith("__init__.py"):
        base = base + [module_id(path).rsplit(".", 1)[-1]] if module_id(path) else base
    base = base[: len(base) - (dots - 1)] if dots > 1 else base
    rest = mod.lstrip(".")
    return ".".join([*base, rest] if rest else base)
