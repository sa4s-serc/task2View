"""Compile every diagram source under runs/ into the same folder as the source."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from task2view.phase4.compile import compile_file

RUNS = ROOT / "runs"
PUML_SUFFIXES = {".puml", ".plantuml"}
SKIP_SUFFIXES = {".png", ".svg", ".jpeg", ".jpg", ".pdf"}
SOURCE_SUFFIXES = {
    ".puml",
    ".plantuml",
    ".mmd",
    ".d2",
    ".dot",
    ".gv",
    ".dsl",
    ".nomnoml",
    ".bpmn",
}


def sources() -> list[Path]:
    found: list[Path] = []
    for path in RUNS.rglob("*"):
        if not path.is_file():
            continue
        name = path.name.lower()
        if name.endswith(".excalidraw.json") or path.suffix.lower() in SOURCE_SUFFIXES:
            if path.suffix.lower() in SKIP_SUFFIXES:
                continue
            found.append(path)
    return sorted(found)


def complete(src: Path) -> bool:
    stem = src.stem
    if src.name.endswith(".excalidraw.json"):
        stem = src.name[: -len(".excalidraw.json")]
        # stem of architecture_view.excalidraw.json is architecture_view.excalidraw
        stem = src.name.replace(".excalidraw.json", "")
    parent = src.parent
    return all((parent / f"{src.stem}.{ext}").exists() for ext in ("png", "svg", "jpeg"))


def jpeg_from_png(png: Path) -> None:
    jpeg = png.with_suffix(".jpeg")
    subprocess.run(
        ["sips", "-s", "format", "jpeg", str(png), "--out", str(jpeg)],
        check=True,
        capture_output=True,
    )


def compile_puml_batch(files: list[Path]) -> None:
    if not files:
        return
    chunk = 25
    for i in range(0, len(files), chunk):
        group = files[i : i + chunk]
        print(f"  plantuml {i + 1}-{i + len(group)} / {len(files)}", flush=True)
        subprocess.run(
            ["plantuml", "-tpng", *[str(p) for p in group]],
            check=True,
        )
        subprocess.run(
            ["plantuml", "-tsvg", *[str(p) for p in group]],
            check=True,
        )
        for src in group:
            png = src.with_suffix(".png")
            if png.exists() and not src.with_suffix(".jpeg").exists():
                jpeg_from_png(png)


def main() -> int:
    all_src = sources()
    pending = [p for p in all_src if not complete(p)]
    puml = []
    other = []
    for path in pending:
        if path.suffix.lower() not in PUML_SUFFIXES:
            other.append(path)
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        if path.stem == "c4plantuml" or "C4/" in text or "C4_Component" in text:
            other.append(path)
        else:
            puml.append(path)
    print(f"sources={len(all_src)} pending={len(pending)} puml={len(puml)} other={len(other)}", flush=True)
    compile_puml_batch(puml)
    reports = []
    for i, path in enumerate(other, start=1):
        print(f"  kroki {i}/{len(other)} {path.relative_to(RUNS)}", flush=True)
        report = compile_file(path, path.parent, formats=["svg", "png", "jpeg"])
        report["source"] = str(path.relative_to(RUNS))
        reports.append(report)
        print(f"    -> {report.get('status')} {report.get('files')}", flush=True)
    out = RUNS / "compile_all_report.json"
    remaining = [str(p.relative_to(RUNS)) for p in sources() if not complete(p)]
    payload = {
        "compiled_puml": len(puml),
        "compiled_other": reports,
        "still_missing": remaining,
    }
    out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"still_missing={len(remaining)} report={out}", flush=True)
    return 0 if not remaining else 1


if __name__ == "__main__":
    raise SystemExit(main())
