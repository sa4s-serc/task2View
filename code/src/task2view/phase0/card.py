"""Phase 0 — build the repository card (deterministic, no model call).

    card = build_card("/path/to/repo")
    card.signals        -> repository signals for viewpoint selection (with evidence)
    render_card(card)   -> the compact text every later agent sees

Design: docs/redesign/02-evidence-and-architecture-model.md §3.
"""

from __future__ import annotations

from collections import Counter
from pathlib import Path

from task2view.contracts.card import EntryPoint, RepositoryCard
from task2view.contracts.models import PipelineError
from task2view.phase0 import facts
from task2view.phase0.corpus import corpus_rules, scan
from task2view.phase0.languages import extractor_for, generic_unit, supported_languages
from task2view.phase0.resolve import Resolver, build_edges
from task2view.phase3.selection import RepoFacts


def build_card(repo: str | Path) -> RepositoryCard:
    root = Path(repo).expanduser().resolve()
    if not root.is_dir():
        raise PipelineError(f"repository path is not a directory: {root}")
    rules = corpus_rules()
    scanned = scan(root)
    card = RepositoryCard(root=str(root), name=root.name, files=[f for _, f in scanned])

    units = []
    unsupported: Counter = Counter()
    for path, f in scanned:
        if f.file_class not in {"code", "test"} or f.language is None:
            continue
        is_test = f.file_class == "test"
        try:
            source = path.read_bytes()
        except OSError:
            continue
        if len(source) > rules["max_parse_bytes"]:
            card.notes.append(f"not parsed (too large): {f.path}")
            continue
        extractor = extractor_for(f.language, f.path)
        if extractor is None:
            unsupported[f.language] += 1
            units.append(generic_unit(f.path, f.language, lines=f.lines, is_test=is_test))
            continue
        try:
            unit = extractor.extract(f.path, source, is_test=is_test)
        except Exception as exc:  # a parser failure on one file must not stop the card
            card.notes.append(f"parse failed: {f.path}: {exc}")
            units.append(generic_unit(f.path, f.language, lines=f.lines, is_test=is_test))
            continue
        f.parsed = True
        units.append(unit)
        if not is_test:
            card.languages[f.language] = card.languages.get(f.language, 0) + 1
    for language, count in unsupported.items():
        card.notes.append(
            f"{count} {language} files: no extractor (supported: {', '.join(sorted(supported_languages()))}); "
            "file-level symbols only, no dependency edges"
        )

    resolver = Resolver(units)
    card.symbols = resolver.symbols
    card.edges = build_edges(units, resolver)
    for unit in units:
        for entry in unit.entries:
            card.entry_points.append(EntryPoint(kind=entry.kind, symbol=entry.symbol, file=unit.path,
                                                line=entry.line, detail=entry.detail))
    card.entry_points.extend(facts.gui_entry_points(card, rules))

    by_class = {cls: [(p, f.path) for p, f in scanned if f.file_class == cls] for cls in
                ("schema", "deploy", "config", "build")}
    card.entities = facts.entities_from_symbols(card.symbols, card.edges, rules) + \
        facts.entities_from_schema(by_class["schema"])
    card.deploy = facts.deploy_units(by_class["deploy"] + by_class["config"])
    card.build = facts.build_units(by_class["build"])
    card.layers = facts.assign_layers(card.symbols, rules)
    imports = sorted({imp.name for unit in units for imp in unit.imports})
    card.signals = facts.derive_signals(card, imports, rules, root)
    return card


def repo_facts(card: RepositoryCard) -> RepoFacts:
    return RepoFacts(signals=set(card.signals))


def fan_in(card: RepositoryCard) -> Counter:
    return Counter(e.target for e in card.edges if e.kind != "imports" and not card.symbols[e.source].is_test)


def render_card(card: RepositoryCard, *, max_items: int = 12) -> str:
    """Compact text summary (the 'repository card') for agent prompts."""
    classes = Counter(f.file_class for f in card.files)
    lines = [f"REPOSITORY {card.name}",
             "languages: " + (", ".join(f"{k} ({v} files)" for k, v in sorted(card.languages.items())) or "none parsed"),
             "files: " + ", ".join(f"{k} {v}" for k, v in sorted(classes.items()))]
    if card.layers:
        lines.append("layers (top to bottom):")
        lines += [f"  {layer}: {', '.join(pk[:4])}{' …' if len(pk) > 4 else ''}" for layer, pk in card.layers.items()]
    eps = card.entry_points
    if eps:
        lines.append(f"entry points ({len(eps)}):")
        lines += [f"  {e.kind} {e.symbol} — {e.detail} ({e.file}:{e.line})" for e in eps[:max_items]]
    if card.entities:
        lines.append(f"persisted entities ({len(card.entities)}):")
        for ent in card.entities[:max_items]:
            fields = ", ".join(f"{f.name}{'*' if f.key else ''}{'→' + (f.target or '').rsplit('.', 1)[-1] if f.relation else ''}"
                               for f in ent.fields[:8])
            lines.append(f"  {ent.name} [{ent.source}] {fields}")
    if card.deploy:
        lines.append("deployment / configuration:")
        lines += [f"  {u.kind} {u.name} {u.details}" for u in card.deploy[:max_items]]
    if card.build:
        lines.append("build:")
        lines += [f"  {b.tool} {b.name or b.file} {b.packaging} deps: {', '.join(b.dependencies[:8])}" for b in card.build[:max_items]]
    top = fan_in(card).most_common(max_items)
    if top:
        lines.append("most depended-on symbols:")
        lines += [f"  {sid} ({n} incoming)" for sid, n in top]
    lines.append("signals: " + ", ".join(sorted(card.signals)))
    if card.notes:
        lines.append("notes: " + "; ".join(card.notes[:5]))
    return "\n".join(lines)
