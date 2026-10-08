# Phase 3 — Viewpoint selection (deterministic)

This is the procedure the pipeline runs in `code/src/task2view/phase3/selection.py`. Follow it step by step; it involves no judgement. Tables are in [catalogs.md](catalogs.md).

## Inputs
- **primary needs** and **secondary needs** from `stakeholder_profile.json`, in the order listed there;
- **subjects** with their needs;
- **role** and **detail_level**;
- the repository **signals** from `repository_card.json`.

## Steps

1. **Clean the needs.** Keep only ids from the catalog, without duplicates. A secondary need that is also primary counts as primary.
   - If there are no primary needs but there are secondary ones, treat all of them as primary and add a note.
   - If there are no needs at all and the role is known, use **every** need at the role's highest prior weight (roles table), and add a note.

2. **Applicable viewpoints.** A viewpoint is applicable if its *applies when* column says `generic`, or the repository has at least one of the listed signals.

3. **Candidates** are the applicable viewpoints that are **not** C&C styles (styles have "style of `cnc-generic`" next to their id) and cover at least one primary need. A viewpoint *covers* the needs in its *frames* and *also covers* columns.

4. **What a set of viewpoints covers:** the union of what each covers, restricted to the primary needs. One extra rule: `layering` also counts as covered when the `layered` viewpoint is applicable and one of the chosen viewpoints lists `layered` in its *overlays* column.

5. **Choose the set.** Consider every set of 1 to 3 candidates (the cap is 3 views). Pick the best set by comparing, in this order:
   1. more primary needs covered;
   2. fewer views;
   3. more secondary needs covered (secondary needs never justify an extra view; they only break ties);
   4. more primary needs *framed* (frames column only, not also covers), summed over the views;
   5. higher role prior: for each view, the highest prior weight among the primary needs it covers, summed;
   6. earlier in the catalog: the smaller sum of the views' positions in the viewpoints table.

6. **Order the views** by the position, in the primary-needs list, of the first need each view covers.

7. **Record what is left.** Primary needs no chosen view covers are `uncovered_needs`. Secondary needs no chosen view covers are `secondary_not_shown`.

8. **For each chosen view:**
   - **needs:** the primary needs it covers, then the secondary needs it covers.
   - **C&C style:** if the view is `cnc-generic`, replace it with the first applicable style in the C&C style order (under the viewpoints table) and set `specialised_from: "cnc-generic"`. The style comes from repository signals, never from the goal's wording.
   - **overlays:** the entries of its *overlays* column whose viewpoint is applicable (in practice `layered` when the repository is layered).
   - **evidence_gap:** if the *evidence* column is non-empty and the repository has none of those signals, write `"no repository evidence of: <signals>"`. The view stays in the plan and is reported as a declared gap.
   - **granularity:** `{"max_elements": <cap for the detail level>}`; for `sequence`, also the allowed fragments for the level.
   - **rationale:** `"<Name> (<V&B ref>) covers <needs>"`, plus the specialisation and overlay reasons when they apply.

9. **Subjects:** put each subject on **every** view whose needs share a need with the subject's needs. If none does, put it on the first view.

## Notes
- A view's needs can include needs it only *also covers*. That is intended: one view answers them, so no second view is added.
- Behaviour viewpoints never cover structural needs, and structural viewpoints never cover behavioural needs. A request for both structure and behaviour therefore gets two views. This rule is built into the catalog.
