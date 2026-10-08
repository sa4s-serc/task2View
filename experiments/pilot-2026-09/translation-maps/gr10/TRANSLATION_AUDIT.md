# GR10 Visual Paradigm English Translation Audit

## Deliverable

- English project: `Software_Engineering_Project_GR10_English.vpp`
- SHA-256:
  `9b39ea4e4ffd028c99de249d8d653bad7c0386f4e9693c5afaa8d3692b6db45d`
- Open it with **Visual Paradigm → File → Open Project**.

The authoritative Italian VPP remains only in the original Italian project at:

`/Users/miryalasathvika/research/CIAO_integragion/italian/progetto_ing_software_gr10-main/docs/visual-paradigm/Progetto_Ing_Software_GR10.vpp`

No Italian VPP is included in the English deliverable. All deliverable `.bak`,
`.vbak`, and numbered VPP backup files were removed. The
`docs/visual-paradigm` folder contains exactly one `.vpp`.

## English-only policy and coverage

This is a view-only English comprehension model. All human-visible UML symbols
and reachable documentation are English, including class/code-style display
identifiers, actors, use cases, requirements, activities, states, transitions,
sequence messages and lifelines, candidates, steps, guards, notes, constraints,
Grid Diagram names, textual analyses, plain text, rich text, and rendered
diagram caches.

The complete project contains 55 diagrams:

- 6 activity diagrams
- 3 class diagrams
- 1 deployment diagram
- 4 Grid Diagrams
- 27 interaction/sequence diagrams
- 1 requirement diagram
- 1 state diagram
- 3 textual-analysis diagrams
- 9 use-case-description diagrams
- 1 use-case diagram

The internal project name is now `Software_Engineering_Project_GR10`.
Generated Grid Diagrams are now named:

- `List of Actors`
- `List of Use Cases`
- `Class List - System Domain Model`
- `Class List - Refined System Domain Model`

The detailed Italian/Java-to-English symbol trace remains available in
`IDENTIFIER_MAPPING.md` and `IDENTIFIER_MAPPING.csv`.

## Transformation workflow

The final XML was produced through schema-aware translation and imported with
Visual Paradigm's bundled `com.vp.cmd.ImportXML`. The resulting project was
re-exported with `com.vp.cmd.ExportXML` for verification.

Visual Paradigm's importer repeatedly restored generated Grid names, the
internal project name, and compressed rich-text/render caches. As the documented
last resort, a transactionally scoped SQLite fallback was applied only to the
English working copy, with before/after VPP backups retained exclusively under
`.dist/gr10-final-cleanup`.

The fallback:

- updated four generated `DIAGRAM` names and serialized headers
- updated `PROJECT_INFO` name and serialized header
- synchronized/translated 17 compressed rich-text files
- translated 45 cached rendered-diagram files (375 displayed values)
- removed one transient recent-message history cache
- corrected three exact embedded candidate/step values

No IDs, references, UML types, cardinalities, geometry, or connectors were
changed. Java code-synchronization metadata was retained as technical
source-traceability data; it is not used as a visible diagram label.

## Validation

- SQLite `PRAGMA integrity_check`: `ok`
- Database model elements: 2,282 before / 2,282 after
- Database diagrams: 55 before / 55 after
- Database diagram elements: 1,496 before / 1,496 after
- Missing/new database model IDs: 0 / 0
- Missing/new database diagram IDs: 0 / 0
- Missing/new database diagram-element IDs: 0 / 0
- Exported model nodes: 5,592 before / 5,592 after
- Exported diagrams: 53 before / 53 after
- Exported shapes: 889 before / 889 after
- Exported connectors: 603 before / 603 after
- Exported diagram references: 1,437 before / 1,437 after
- Missing/new exported IDs: 0 / 0

Comprehensive post-export scans covered every XML attribute plus diagram/model
names, documentation, properties, notes, candidates, steps, labels, guards,
messages, constraints, compressed rich text, and rendered diagram caches.

**Final human-visible Italian residual count: 0**

The four pre-existing orphan shapes reported by Visual Paradigm remain
preserved:

- Create New Report - Refined
- Create New Report - BCED Pattern
- Monitor Activity Progress - BCED Pattern
- Update Report Status - BCED Pattern

## Visual validation

The `validation-images` folder contains fresh CLI-rendered images for every
graphic diagram category supported by `ExportDiagramImage`, including activity,
sequence, class, deployment, requirement, state, and use-case diagrams.
Grid, textual-analysis, and use-case-description diagrams are not emitted by
that CLI, so those categories were validated through their exported XML,
SQLite names, and rich-text properties.
