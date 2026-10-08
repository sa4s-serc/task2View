# Quality rules (published grain)

Source of truth: [knowledge/view_projection.yaml](../knowledge/view_projection.yaml).

## Naming

- Name boxes by **responsibility** using repository type stems (`ReservationManager`, `LibraryFacade`, `UserRegistry`).
- Never use layout folders as architecture: `boundary`, `controller`, `control`, `dto`, `entity`, `gui`.
- Never use Java packages (`it.unina.reservations…`) as element names.
- Never use a GUI filename as the system (`ActivityMonitoringGUI.java`). Use a product-level name grounded in README / root package / artifact id.
- Cap published elements at the stakeholder `max_elements_per_view` (usually 8–20). Prefer 6–12.

## Grain by viewpoint

| viewpoint_id | nodes | relations | forbid |
|---|---|---|---|
| context | actors, one system, externals, boundary datastores | actor-to-system `uses` | internal classes, GUIs, packages as the system |
| module-decomposition | subsystems that own the task | `contains` or `uses` | one box per file; class inventory |
| cnc-runtime | runtime components and connectors | connectors | source packages as runtime nodes |
| code-mapping | architecture elements mapped to implementing types | implements / located-in | entire-repository class dump |
| allocation-deployment | artifacts, nodes, datastores | `deploys` / communicates | classes as nodes |
| decision-record | components affected by recorded decisions | depends | inventing decisions not in the repo |

## Evidence

- `evidence.file` is a path relative to `--code` and must be in `repository_scope.json`.
- `excerpt` is a short real snippet (signature, annotation, compose service, SQL table).
- `support`: `observed` if the excerpt shows the claim; `inferred` otherwise. Testers, architects, analysts, and operators: prefer `declare-gap` over inference (`on_missing_evidence` on the stakeholder profile).
- Relations need both ends in `elements`. Prefer an excerpt that shows the call, import, FK, or deploy mapping.

## Choice stands

The viewpoint chosen in phase 2 is the winner. Do not retarget it because later questions sound structural or behavioural. Questions are written after the choice and must stay inside that grain. `integration test` is not a second chance to switch viewpoints.
