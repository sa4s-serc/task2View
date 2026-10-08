# Pilot study, September 2026

Three conditions, two systems, ten stakeholder goals. Write-up: [`docs/overleaf/main.tex`](../../docs/overleaf/main.tex). Root-cause analysis of the Task2View outputs: [`docs/design-review-2026-10.md`](../../docs/design-review-2026-10.md).

The subjects are the English systems in `data/` (gitignored): `Progetto-IS-main-English` and `progetto_ing_software_gr10-main-English`. Goals: [`docs/input_example_task2view.txt`](../../docs/input_example_task2view.txt). Evaluation site: [`docs/evaluation/`](../../docs/evaluation).

## Layout

| Path | What it is |
|---|---|
| `outputs/task2view/` | Task2View pipeline batch of 24 Sep on the English systems. Not reviewed. |
| `outputs/skill-agent/english-rerun/` | Agent + [`skill/`](../../skill) on the English systems |
| `outputs/plain-agent/english-rerun/` | Plain agent on the English systems |
| `outputs/skill-agent/italian-reviewed/` | **The set the expert reviewed** (see below) |
| `outputs/plain-agent/italian-reviewed/` | **The set the expert reviewed** (see below) |
| `review/comparison_review.txt` | The expert's 18 comments: Folder 1 = skill agent, Folder 2 = plain agent |
| `translation-maps/` | Identifier maps between the reviewed runs and the English systems |
| `manifest.json` | Goal text and output paths of the agent runs, as originally run |

## Why two agent sets

The agent runs that the expert reviewed were made on the original Italian-language code of the two systems, not on the English systems. The review quotes identifiers that occur only there (`Segnalazione`, `id_cittadino`, `BoundaryAutenticazione POST /api/auth/registrazione`). The `english-rerun` folders are the same conditions re-run on the English systems about 10 minutes later. They differ in content as well as in names, so the review cannot be applied to them as-is. Use `translation-maps/` to relate a reviewed element to its English counterpart.

The original code is not kept in this repository. To reproduce the reviewed runs, use `github.com/CapHello/Progetto-IS` @ `070e4fc` and `github.com/Sal-zip/progetto_ing_software_gr10` @ `63b0160`.

`main.tex` and the pipeline spec §11–12 say all conditions ran on the English systems. That holds only for Task2View and the `english-rerun` folders.

## Notes on the Task2View batch

- The runs record `scope_strategy: pagerank`, but every scoped file has origin `ri_forced` (2–8 files): the Phase 4 plan filters out PageRank candidates. See design review RC2.
- The batch predates the code on branch `wip/phase-renumbering`; several phases changed after 24 Sep.
- Absolute paths inside run artifacts (`batch_summary.json`, `normalized_request.json`, `manifest.json`) are the original locations and are left unchanged.
