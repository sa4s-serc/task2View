# Pilot study, September 2026

Three conditions, two systems, ten stakeholder goals. Write-up: [`docs/overleaf/main.tex`](../../docs/overleaf/main.tex). Root-cause analysis of the Task2View outputs: [`docs/design-review-2026-10.md`](../../docs/design-review-2026-10.md).

## Layout

| Path | What it is |
|---|---|
| `manifest.json` | Goal text and paths used for the two agent conditions (original absolute paths, kept as run) |
| `review/comparison_review.txt` | The expert's 18 comments on the skill agent (Folder 1) and plain agent (Folder 2) |
| `outputs/skill-agent/italian-reviewed/` | Agent + [`skill/`](../../skill) on the **Italian** code. **This is the set the expert reviewed.** |
| `outputs/skill-agent/english-rerun/` | Same condition re-run on the English variant about 10 minutes later. Was `comparison/folder1`. |
| `outputs/plain-agent/italian-reviewed/` | Plain agent on the **Italian** code (diagram + `notes.md`). **Reviewed.** |
| `outputs/plain-agent/english-rerun/` | English re-run. Was `comparison/folder2`. |
| `outputs/task2view/` | Task2View pipeline batch of 24 Sep on the English variants. Was `code/runs/pilot`; its PNGs were `comparison/folder3`. Not reviewed. |

Goals: [`docs/input_example_task2view.txt`](../../docs/input_example_task2view.txt). Evaluation site: [`docs/evaluation/`](../../docs/evaluation).

## Provenance (checked 2026-10-08)

- **The review matches the Italian runs.** The comments quote `Segnalazione`, `Cittadino`, `id_cittadino` and `BoundaryAutenticazione POST /api/auth/registrazione`. These occur only in `*/italian-reviewed/`. The English re-runs differ in content, not only in names (for example, skill IS-reg-L3 has 7 boxes in Italian and 8 in English). `main.tex` and the pipeline spec §11–12 say all conditions ran on the English variants. That holds for Task2View only.
- **Italian subjects** (deleted locally; re-clone to reproduce):
  - Progetto-IS: `https://github.com/CapHello/Progetto-IS` @ `070e4fccd95a804b8da4a16c782f76be1cd39762`
  - GR10: `https://github.com/Sal-zip/progetto_ing_software_gr10` @ `63b01606a7717b001acf5fddab22ea56d3449fcb`
- **English subjects:** `data/Progetto-IS-main-English`, `data/progetto_ing_software_gr10-main-English` (translations of the above with `CODE_TRANSLATION_MAP.*`). `data/` is gitignored.
- **Task2View scope label.** The runs record `scope_strategy: pagerank`, but every scoped file has origin `ri_forced` (2–8 files). PageRank candidates are filtered out by the Phase 4 plan. See design review RC2.
- **Code version.** The Task2View outputs predate the code on branch `wip/phase-renumbering` (commit `eb11b1d`). Several phases changed after 24 Sep.
- Absolute paths inside run artifacts (`batch_summary.json`, `normalized_request.json`, `manifest.json`) are the original locations and are left unchanged.
