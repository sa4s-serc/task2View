"""Extract structural facts from a Java source tree with javalang.

Produces the code-side reference used to check whether relations drawn in UML
are actually present in the implementation: inheritance, field/param typing,
instantiation, and resolved method calls between project classes.
"""

import os
import re
from collections import defaultdict

import javalang

# javalang predates Java 16 pattern-matching instanceof. Structural facts do not
# depend on the binding variable, so drop it to keep the file parseable.
INSTANCEOF_PATTERN = re.compile(
    r"\binstanceof\s+((?:final\s+)?[A-Za-z_$][\w$.]*(?:\s*<[^<>()]*(?:<[^<>()]*>)?[^<>()]*>)?)"
    r"\s+([a-z_$][\w$]*)\b"
)


def normalize_source(src):
    """Rewrite modern syntax javalang cannot parse. Returns (source, n_rewrites)."""
    src, n = INSTANCEOF_PATTERN.subn(r"instanceof \1", src)
    return src, n

PRIMITIVES = {
    "int", "long", "double", "float", "boolean", "char", "byte", "short", "void",
    "String", "Object", "List", "ArrayList", "Map", "HashMap", "Set", "HashSet",
    "Date", "LocalDate", "LocalDateTime", "Integer", "Long", "Double", "Boolean",
    "Exception", "IllegalArgumentException", "RuntimeException",
}


def parse_tree(root):
    units, rewritten = {}, {}
    for dirpath, _, files in os.walk(root):
        for fn in files:
            if not fn.endswith(".java"):
                continue
            path = os.path.join(dirpath, fn)
            with open(path, encoding="utf8", errors="replace") as fh:
                src = fh.read()
            src, n = normalize_source(src)
            if n:
                rewritten[path] = n
            try:
                units[path] = javalang.parse.parse(src)
            except Exception as exc:  # unparsable file: record and skip
                units[path] = exc
    return units, rewritten


class JavaFacts:
    def __init__(self, root):
        self.root = root
        self.units, self.rewritten = parse_tree(root)
        self.failed = {p: u for p, u in self.units.items() if isinstance(u, Exception)}
        self.classes = {}          # name -> {"path", "extends", "implements", "fields", "methods"}
        self.extends = {}          # sub -> super
        self.implements = defaultdict(set)
        self.field_types = defaultdict(set)   # class -> {type}
        self.instantiates = defaultdict(set)  # class -> {type}
        self.calls = defaultdict(set)         # class -> {(target_class, method)}
        self._build()

    def _build(self):
        for path, tree in self.units.items():
            if isinstance(tree, Exception):
                continue
            for _, node in tree.filter(javalang.tree.TypeDeclaration):
                self._class(path, node)

    def _class(self, path, node):
        name = node.name
        self.classes[name] = {
            "path": os.path.relpath(path, self.root),
            "kind": type(node).__name__,
        }
        ext = getattr(node, "extends", None)
        if ext is not None:
            base = ext[0].name if isinstance(ext, list) else ext.name
            self.extends[name] = base
        for impl in getattr(node, "implements", None) or []:
            self.implements[name].add(impl.name)

        # field and local declarations give "knows about type" edges
        for kind in (javalang.tree.FieldDeclaration, javalang.tree.LocalVariableDeclaration):
            for _, d in node.filter(kind):
                t = getattr(d.type, "name", None)
                if t:
                    self.field_types[name].add(t)
        for _, p in node.filter(javalang.tree.FormalParameter):
            t = getattr(p.type, "name", None)
            if t:
                self.field_types[name].add(t)
        for _, c in node.filter(javalang.tree.ClassCreator):
            t = getattr(c.type, "name", None)
            if t:
                self.instantiates[name].add(t)

        # method calls, resolved through the declared type of the receiver
        var_types = {}
        for kind in (
            javalang.tree.FieldDeclaration,
            javalang.tree.LocalVariableDeclaration,
            javalang.tree.FormalParameter,
        ):
            for _, d in node.filter(kind):
                t = getattr(d.type, "name", None)
                decls = getattr(d, "declarators", None) or [d]
                for dec in decls:
                    if getattr(dec, "name", None) and t:
                        var_types[dec.name] = t
        for _, inv in node.filter(javalang.tree.MethodInvocation):
            recv = inv.qualifier
            if not recv:
                continue
            target = var_types.get(recv, recv)  # variable -> its type, else a static class ref
            self.calls[name].add((target, inv.member))

    def known(self, t):
        return t in self.classes

    def uses(self, a, b):
        """True when class a references class b in any structural way."""
        return (
            b in self.field_types.get(a, ())
            or b in self.instantiates.get(a, ())
            or any(t == b for t, _ in self.calls.get(a, ()))
            or self.extends.get(a) == b
            or b in self.implements.get(a, ())
        )

    def call_targets(self, a):
        return {t for t, _ in self.calls.get(a, ()) if self.known(t)}
