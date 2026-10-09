"""JavaScript / TypeScript extractor (tree-sitter-javascript, tree-sitter-typescript).

Declares: one module symbol per file, classes (with extends), top-level
functions. References: ES imports and ``require`` of relative modules, extends,
calls to imported names, ``new`` of imported or local classes.
Entry points: Express-style routes (``app.get('/x', …)``, ``router.post(…)``).
"""

from __future__ import annotations

import posixpath

import tree_sitter as ts
import tree_sitter_javascript as tsjs
import tree_sitter_typescript as tsts

from task2view.contracts.card import Method, Symbol
from task2view.phase0.languages.base import FileUnit, Import, LanguageExtractor, RawEntry, RawRef, text, walk

_HTTP = {"get", "post", "put", "delete", "patch", "all", "use"}
_EXTS = (".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs")


def module_id(path: str) -> str:
    stem = path
    for ext in _EXTS:
        if stem.endswith(ext):
            stem = stem[: -len(ext)]
            break
    if stem.endswith("/index"):
        stem = stem[: -len("/index")]
    return stem.replace("/", ".")


def _resolve(spec: str, path: str) -> str:
    if not spec.startswith("."):
        return spec  # package import: kept as written, never internal
    joined = posixpath.normpath(posixpath.join(posixpath.dirname(path), spec))
    return module_id(joined)


class JavaScriptExtractor(LanguageExtractor):
    language = "javascript"

    def __init__(self, typescript: bool = False, tsx: bool = False):
        if typescript:
            lang = ts.Language(tsts.language_tsx() if tsx else tsts.language_typescript())
            self.language = "typescript"
        else:
            lang = ts.Language(tsjs.language())
        self._parser = ts.Parser(lang)

    def extract(self, path: str, source: bytes, *, is_test: bool) -> FileUnit:
        root = self._parser.parse(source).root_node
        mid = module_id(path)
        unit = FileUnit(path=path, language=self.language, package=mid.rsplit(".", 1)[0] if "." in mid else "")
        unit.symbols.append(Symbol(id=mid, name=mid.rsplit(".", 1)[-1], kind="module", file=path, start_line=1,
                                   end_line=root.end_point[0] + 1, language=self.language, package=unit.package,
                                   is_test=is_test))
        local: dict[str, str] = {}
        for n in walk(root):
            if n.type == "import_statement":
                src_node = n.child_by_field_name("source")
                if src_node is None:
                    continue
                target = _resolve(text(src_node, source).strip("'\"`"), path)
                unit.imports.append(Import(target, n.start_point[0] + 1))
                unit.refs.append(RawRef(mid, target, "imports", n.start_point[0] + 1))
                for spec in walk(n):
                    if spec.type == "import_specifier":
                        name = spec.child_by_field_name("name")
                        alias = spec.child_by_field_name("alias") or name
                        if name is not None:
                            local[text(alias, source)] = f"{target}.{text(name, source)}"
                    elif spec.type in {"import_clause", "namespace_import"}:
                        for ident in spec.children:
                            if ident.type == "identifier":
                                # `* as ns` binds the module; a default import binds the module's symbol of the
                                # same name when there is one (resolution falls back to the module otherwise)
                                name = text(ident, source)
                                local[name] = target if spec.type == "namespace_import" else f"{target}.{name}"
            elif n.type == "call_expression":
                fn = n.child_by_field_name("function")
                args = n.child_by_field_name("arguments")
                if fn is not None and text(fn, source) == "require" and args is not None and args.named_child_count:
                    target = _resolve(text(args.named_children[0], source).strip("'\"`"), path)
                    unit.imports.append(Import(target, n.start_point[0] + 1))
                    unit.refs.append(RawRef(mid, target, "imports", n.start_point[0] + 1))
                    parent = n.parent
                    if parent is not None and parent.type == "variable_declarator":
                        name = parent.child_by_field_name("name")
                        if name is not None and name.type == "identifier":
                            local[text(name, source)] = target
                elif fn is not None and fn.type == "member_expression" and args is not None and args.named_child_count:
                    prop = fn.child_by_field_name("property")
                    first = args.named_children[0]
                    if prop is not None and text(prop, source) in _HTTP and first.type in {"string", "template_string"}:
                        route = text(first, source).strip("'\"`")
                        if route.startswith("/"):
                            unit.entries.append(RawEntry("http-route", mid, n.start_point[0] + 1, f"{text(prop, source).upper()} {route}"))

        for child in root.children:
            node = child.child_by_field_name("declaration") if child.type == "export_statement" else child
            if node is None:
                continue
            if node.type in {"class_declaration", "class"}:
                self._class(node, source, unit, mid, local, is_test)
            elif node.type == "function_declaration":
                self._function(node, text(node.child_by_field_name("name"), source), source, unit, mid, local, is_test)
            elif node.type in {"lexical_declaration", "variable_declaration"} and _arrow(node):
                decl = _arrow(node)  # const f = () => ...
                self._function(decl.child_by_field_name("value"), text(decl.child_by_field_name("name"), source),
                               source, unit, mid, local, is_test)
            elif node.type != "import_statement":  # top-level statements: app.use(new Router()), wiring code
                self._calls(node, source, unit, mid, Method(name="<module>", start_line=node.start_point[0] + 1,
                                                            end_line=node.end_point[0] + 1), local)
        return unit

    def _function(self, node, name: str, src: bytes, unit: FileUnit, mid: str, local, is_test: bool) -> None:
        local.setdefault(name, f"{mid}.{name}")
        fn = Symbol(id=f"{mid}.{name}", name=name, kind="function", file=unit.path,
                    start_line=node.start_point[0] + 1, end_line=node.end_point[0] + 1,
                    language=self.language, package=mid, is_test=is_test)
        method = Method(name=name, start_line=fn.start_line, end_line=fn.end_line)
        self._calls(node, src, unit, fn.id, method, local)
        fn.methods.append(method)
        unit.symbols.append(fn)

    def _class(self, node, src: bytes, unit: FileUnit, mid: str, local, is_test: bool) -> None:
        name_node = node.child_by_field_name("name")
        if name_node is None:
            return
        name = text(name_node, src)
        sid = f"{mid}.{name}"
        local.setdefault(name, sid)
        symbol = Symbol(id=sid, name=name, kind="class", file=unit.path, start_line=node.start_point[0] + 1,
                        end_line=node.end_point[0] + 1, language=self.language, package=mid, is_test=is_test)
        for child in node.children:
            if child.type == "class_heritage" and child.named_children:
                base = text(child.named_children[0], src)  # Base or ns.Base
                head, _, tail = base.partition(".")
                symbol.extends.append(base)
                unit.refs.append(RawRef(sid, local.get(head, head) + (f".{tail}" if tail else ""), "extends",
                                        child.start_point[0] + 1))
        body = node.child_by_field_name("body")
        for m in (body.children if body else []):
            if m.type == "method_definition":
                mname = text(m.child_by_field_name("name"), src)
                method = Method(name=mname, start_line=m.start_point[0] + 1, end_line=m.end_point[0] + 1)
                self._calls(m, src, unit, sid, method, local)
                symbol.methods.append(method)
        unit.symbols.append(symbol)

    def _calls(self, node, src: bytes, unit: FileUnit, source_id: str, method: Method, local) -> None:
        for n in walk(node):
            if n.type == "new_expression":
                ctor = n.child_by_field_name("constructor")
                if ctor is not None and text(ctor, src) in local:
                    unit.refs.append(RawRef(source_id, local[text(ctor, src)], "instantiates", n.start_point[0] + 1, method.name))
            elif n.type == "call_expression":
                fn = n.child_by_field_name("function")
                if fn is None:
                    continue
                head = text(fn, src).split(".", 1)[0]
                if head in local:
                    target = local[head] + ("." + text(fn, src).split(".", 1)[1] if "." in text(fn, src) else "")
                    unit.refs.append(RawRef(source_id, target, "calls", n.start_point[0] + 1, method.name))


def _arrow(node):
    """The declarator of `const f = () => ...` / `= function () {}`, else None."""
    decl = next((c for c in node.named_children if c.type == "variable_declarator"), None)
    value = decl.child_by_field_name("value") if decl is not None else None
    name = decl.child_by_field_name("name") if decl is not None else None
    ok = value is not None and value.type in {"arrow_function", "function_expression", "function"}
    return decl if ok and name is not None and name.type == "identifier" else None
