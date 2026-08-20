"""Compile diagram source to SVG / PNG / JPEG (Kroki, with local fallbacks).

Pipeline spec v2 Stage 4b: adapters emit text; this module rasterises it.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import urllib.error
import urllib.request
from pathlib import Path
from typing import Iterable

DEFAULT_KROKI_URL = os.environ.get("KROKI_URL", "https://kroki.io")
DEFAULT_FORMATS = ("svg", "png", "jpeg")

KROKI_TYPE = {
    "plantuml": "plantuml",
    "c4plantuml": "c4plantuml",
    "mermaid": "mermaid",
    "d2": "d2",
    "graphviz": "graphviz",
    "structurizr": "structurizr",
    "nomnoml": "nomnoml",
    "excalidraw": "excalidraw",
    "bpmn": "bpmn",
}

SOURCE_EXT = {
    ".puml": "plantuml",
    ".plantuml": "plantuml",
    ".mmd": "mermaid",
    ".d2": "d2",
    ".dot": "graphviz",
    ".gv": "graphviz",
    ".dsl": "structurizr",
    ".nomnoml": "nomnoml",
    ".bpmn": "bpmn",
    ".excalidraw.json": "excalidraw",
}

_MIME = {
    "svg": "image/svg+xml",
    "png": "image/png",
    "jpeg": "image/jpeg",
    "jpg": "image/jpeg",
    "pdf": "application/pdf",
}


def normalize_format(fmt: str) -> str:
    name = fmt.strip().lower().lstrip(".")
    if name == "jpg":
        return "jpeg"
    if name not in {"svg", "png", "jpeg", "pdf"}:
        raise ValueError(f"unsupported render format {fmt!r}")
    return name


def parse_formats(text: str | None) -> list[str]:
    if not text or not text.strip():
        return list(DEFAULT_FORMATS)
    return [normalize_format(part) for part in text.split(",") if part.strip()]


def infer_notation(path: Path, source: str | None = None) -> str:
    name = path.name.lower()
    if name.endswith(".excalidraw.json") or name.endswith(".excalidraw"):
        return "excalidraw"
    if path.stem in KROKI_TYPE:
        return path.stem
    notation = SOURCE_EXT.get(path.suffix.lower())
    blob = source if source is not None else path.read_text(encoding="utf-8", errors="replace")
    if notation == "plantuml" and ("C4/" in blob or "C4_Component" in blob or "C4_Container" in blob):
        return "c4plantuml"
    if notation:
        return notation
    raise ValueError(f"cannot infer diagram language from {path}")


def _kroki_post(diagram_type: str, fmt: str, source: str, *, url: str, timeout: int) -> bytes:
    endpoint = f"{url.rstrip('/')}/{diagram_type}/{fmt}"
    req = urllib.request.Request(
        endpoint,
        data=source.encode("utf-8"),
        headers={"Content-Type": "text/plain", "Accept": _MIME.get(fmt, "*/*")},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def _png_to_jpeg(png: bytes, dest: Path) -> None:
    sips = shutil.which("sips")
    if not sips:
        raise RuntimeError("jpeg conversion needs Kroki jpeg support or macOS sips")
    dest.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        png_path = Path(tmp) / "in.png"
        png_path.write_bytes(png)
        subprocess.run(
            [sips, "-s", "format", "jpeg", str(png_path), "--out", str(dest)],
            check=True,
            capture_output=True,
        )


def _local_render(notation: str, source: str, fmt: str) -> bytes | None:
    """Best-effort local compilers when Kroki is unavailable."""
    if fmt == "jpeg":
        png = _local_render(notation, source, "png")
        if not png:
            return None
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "out.jpeg"
            try:
                _png_to_jpeg(png, dest)
            except (OSError, RuntimeError, subprocess.CalledProcessError):
                return None
            return dest.read_bytes() if dest.exists() else None

    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        if notation in {"plantuml", "c4plantuml"} and shutil.which("plantuml"):
            src = tmp_dir / "in.puml"
            src.write_text(source, encoding="utf-8")
            flag = {"png": "-tpng", "svg": "-tsvg", "pdf": "-tpdf"}[fmt]
            subprocess.run(
                ["plantuml", flag, "-o", str(tmp_dir), str(src)],
                check=True,
                capture_output=True,
            )
            produced = next(tmp_dir.glob(f"in.{fmt if fmt != 'jpeg' else 'png'}"), None)
            return produced.read_bytes() if produced else None
        if notation == "graphviz" and shutil.which("dot"):
            proc = subprocess.run(
                ["dot", f"-T{fmt}"],
                input=source.encode("utf-8"),
                check=True,
                capture_output=True,
            )
            return proc.stdout
        if notation == "mermaid" and shutil.which("mmdc"):
            src = tmp_dir / "in.mmd"
            out = tmp_dir / f"out.{fmt}"
            src.write_text(source, encoding="utf-8")
            subprocess.run(
                ["mmdc", "-i", str(src), "-o", str(out), "-q"],
                check=True,
                capture_output=True,
            )
            return out.read_bytes() if out.exists() else None
    return None


def render_bytes(
    source: str,
    notation: str,
    fmt: str,
    *,
    kroki_url: str | None = None,
    timeout: int = 90,
    fetch=None,
) -> tuple[bytes, str]:
    """Return (payload, backend). backend is 'kroki', 'kroki+sips', or 'local'."""
    fmt = normalize_format(fmt)
    kroki_type = KROKI_TYPE.get(notation)
    if not kroki_type:
        raise ValueError(f"no compiler registered for notation {notation!r}")
    url = kroki_url or DEFAULT_KROKI_URL
    post = fetch or _kroki_post
    try:
        return post(kroki_type, fmt, source, url=url, timeout=timeout), "kroki"
    except urllib.error.HTTPError as exc:
        if fmt == "jpeg":
            try:
                png, _backend = render_bytes(
                    source, notation, "png", kroki_url=url, timeout=timeout, fetch=fetch
                )
                with tempfile.TemporaryDirectory() as tmp:
                    dest = Path(tmp) / "out.jpeg"
                    _png_to_jpeg(png, dest)
                    return dest.read_bytes(), "kroki+sips"
            except Exception:
                pass
        detail = exc.read().decode("utf-8", errors="replace")[:400]
        local = _local_render(notation, source, fmt)
        if local:
            return local, "local"
        raise RuntimeError(f"Kroki HTTP {exc.code} for {notation}/{fmt}: {detail}") from exc
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        local = _local_render(notation, source, fmt)
        if local:
            return local, "local"
        raise RuntimeError(f"Kroki request failed for {notation}/{fmt}: {exc}") from exc


def compile_diagram(
    source: str,
    notation: str,
    out_dir: Path,
    *,
    stem: str = "architecture_view",
    formats: Iterable[str] = DEFAULT_FORMATS,
    kroki_url: str | None = None,
    fetch=None,
) -> dict:
    """Write compiled images next to the diagram source. Never raises on a single format miss."""
    out_dir.mkdir(parents=True, exist_ok=True)
    wanted = [normalize_format(fmt) for fmt in formats]
    files: dict[str, str] = {}
    errors: dict[str, str] = {}
    backends: dict[str, str] = {}
    png_bytes: bytes | None = None
    for fmt in wanted:
        try:
            payload, backend = render_bytes(
                source, notation, fmt, kroki_url=kroki_url, fetch=fetch
            )
            if fmt == "png":
                png_bytes = payload
            dest = out_dir / f"{stem}.{fmt}"
            dest.write_bytes(payload)
            files[fmt] = dest.name
            backends[fmt] = backend
        except Exception as exc:
            if fmt == "jpeg" and png_bytes:
                try:
                    dest = out_dir / f"{stem}.jpeg"
                    _png_to_jpeg(png_bytes, dest)
                    files[fmt] = dest.name
                    backends[fmt] = "sips"
                    continue
                except Exception as conv_exc:
                    errors[fmt] = str(conv_exc)
                    continue
            errors[fmt] = str(exc)
    return {
        "notation": notation,
        "formats": wanted,
        "files": files,
        "backends": backends,
        "errors": errors,
        "status": "ok" if files and not errors else ("partial" if files else "fail"),
    }


def compile_file(
    path: Path,
    out_dir: Path | None = None,
    *,
    notation: str | None = None,
    formats: Iterable[str] = DEFAULT_FORMATS,
    kroki_url: str | None = None,
    fetch=None,
) -> dict:
    source = path.read_text(encoding="utf-8", errors="replace")
    lang = notation or infer_notation(path, source)
    dest = out_dir or path.parent
    return compile_diagram(
        source,
        lang,
        dest,
        stem=path.stem,
        formats=formats,
        kroki_url=kroki_url,
        fetch=fetch,
    )


def discover_sources(run_dir: Path, *, all_notations: bool = False) -> list[Path]:
    found: list[Path] = []
    for pattern in (
        "architecture_view.puml",
        "architecture_view.mmd",
        "architecture_view.d2",
        "architecture_view.dot",
        "architecture_view.dsl",
        "architecture_view.nomnoml",
        "architecture_view.bpmn",
        "architecture_view.excalidraw.json",
    ):
        hit = run_dir / pattern
        if hit.exists():
            found.append(hit)
    if all_notations:
        notations = run_dir / "notations"
        if notations.is_dir():
            for child in sorted(notations.iterdir()):
                if child.is_file() and child.suffix.lstrip(".") not in {"svg", "png", "jpeg", "jpg", "pdf"}:
                    found.append(child)
    return found


def compile_run_dir(
    run_dir: Path,
    *,
    formats: Iterable[str] = DEFAULT_FORMATS,
    all_notations: bool = False,
    kroki_url: str | None = None,
    fetch=None,
) -> dict:
    reports = []
    for path in discover_sources(run_dir, all_notations=all_notations):
        reports.append(
            {
                "source": str(path.relative_to(run_dir)),
                **compile_file(
                    path,
                    path.parent,
                    formats=formats,
                    kroki_url=kroki_url,
                    fetch=fetch,
                ),
            }
        )
    if not reports:
        return {"status": "fail", "error": f"no diagram source in {run_dir}", "diagrams": []}
    statuses = {item.get("status") for item in reports}
    status = "ok" if statuses == {"ok"} else ("fail" if statuses == {"fail"} else "partial")
    return {"status": status, "diagrams": reports}
