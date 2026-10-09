"""Copy a subject repository for an experiment run, without the files no condition may read.

Removes UML models and exported diagrams (they are the evaluation reference), other
binaries (images, PDFs, archives), and VCS / build folders, using the same corpus
rules as the pipeline's Phase 0. Writes <dst>.PREPARED.json next to the copy (not inside
it, where Phase 0 would read the names of the removed diagrams) listing what was left out.

    .venv/bin/python scripts/prepare_subject.py --src ../data/<repo> --dst /tmp/t2v-subjects/<run-id>/<repo>
"""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

from task2view.phase0.corpus import scan

EXCLUDED_CLASSES = {"model", "binary"}


def prepare(src: Path, dst: Path) -> dict:
    if dst.exists() and any(dst.iterdir()):
        raise SystemExit(f"destination {dst} is not empty; use a fresh folder per run")
    copied, removed = 0, []
    for path, f in scan(src):
        if f.file_class in EXCLUDED_CLASSES:
            removed.append({"path": f.path, "class": f.file_class})
            continue
        target = dst / f.path
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)
        copied += 1
    record = {"source": str(src.resolve()), "copied_files": copied, "removed": removed,
              "rule": "files classified as model or binary by knowledge/data/vb/corpus.yaml"}
    dst.mkdir(parents=True, exist_ok=True)
    dst.with_name(f"{dst.name}.PREPARED.json").write_text(json.dumps(record, indent=2), encoding="utf-8")
    return record


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--src", required=True)
    parser.add_argument("--dst", required=True)
    args = parser.parse_args()
    record = prepare(Path(args.src), Path(args.dst))
    print(f"copied {record['copied_files']} files; removed {len(record['removed'])} model/binary files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
