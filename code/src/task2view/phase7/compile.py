"""Render diagram sources to images.

Local PlantUML first (ADR-008: every view is UML). A Kroki server is used only when its
URL is given explicitly, because diagram sources describe the analysed code and
should not leave the machine by default.
"""

from __future__ import annotations

import shutil
import subprocess
import tempfile
import urllib.error
import urllib.request
from pathlib import Path

FORMATS = ("svg", "png", "pdf")
_KROKI_TYPE = {"plantuml": "plantuml"}  # ADR-008: every view is UML in PlantUML


def parse_formats(text: str | None) -> list[str]:
    formats = [part.strip().lower() for part in (text or "").split(",") if part.strip()] or ["svg"]
    unknown = [f for f in formats if f not in FORMATS]
    if unknown:
        raise ValueError(f"unsupported image formats {unknown}; use {', '.join(FORMATS)}")
    return formats


def notation_of(path: Path) -> str:
    """The run writer names files view.puml (PlantUML) or view.<notation>.<ext>."""
    parts = path.name.split(".")
    return parts[1] if len(parts) >= 3 else "plantuml"


def _local(notation: str, source: str, fmt: str) -> bytes | None:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        if notation == "plantuml" and shutil.which("plantuml"):
            src = tmp_dir / "in.puml"
            src.write_text(source, encoding="utf-8")
            subprocess.run(["plantuml", f"-t{fmt}", "-o", str(tmp_dir), str(src)], check=True, capture_output=True)
            out = tmp_dir / f"in.{fmt}"
            return out.read_bytes() if out.exists() else None
    return None


def _kroki(url: str, notation: str, source: str, fmt: str) -> bytes:
    request = urllib.request.Request(f"{url.rstrip('/')}/{_KROKI_TYPE[notation]}/{fmt}", data=source.encode("utf-8"),
                                     headers={"Content-Type": "text/plain"}, method="POST")
    with urllib.request.urlopen(request, timeout=90) as response:
        return response.read()


def render(source: str, notation: str, fmt: str, *, kroki_url: str | None = None) -> tuple[bytes, str]:
    """(image bytes, backend). Raises RuntimeError when no backend can render it."""
    try:
        data = _local(notation, source, fmt)
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(f"local {notation} compiler failed: {exc.stderr.decode('utf-8', 'replace')[:300]}") from exc
    if data:
        return data, "local"
    if kroki_url and notation in _KROKI_TYPE:
        try:
            return _kroki(kroki_url, notation, source, fmt), "kroki"
        except (urllib.error.URLError, TimeoutError) as exc:
            raise RuntimeError(f"Kroki failed for {notation}/{fmt}: {exc}") from exc
    raise RuntimeError(f"no local compiler for {notation}; pass --kroki-url to render it remotely")


def compile_run_dir(run_dir: Path, *, formats: list[str], kroki_url: str | None = None) -> dict:
    files, errors = [], []
    sources = sorted(p for p in run_dir.glob("V*/view*.*") if p.suffix.lstrip(".") not in FORMATS and p.name != "view.json")
    for src in sources:
        notation = notation_of(src)
        for fmt in formats:
            dest = src.with_suffix(f".{fmt}") if src.name == "view.puml" else src.parent / f"view.{notation}.{fmt}"
            try:
                data, backend = render(src.read_text(encoding="utf-8"), notation, fmt, kroki_url=kroki_url)
            except RuntimeError as exc:
                errors.append(f"{src.relative_to(run_dir)} -> {fmt}: {exc}")
                continue
            dest.write_bytes(data)
            files.append({"file": str(dest.relative_to(run_dir)), "backend": backend})
    status = "fail" if not files else "partial" if errors else "ok"
    return {"status": status, "files": files, "errors": errors}
