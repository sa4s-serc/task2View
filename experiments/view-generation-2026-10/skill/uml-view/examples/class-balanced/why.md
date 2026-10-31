# Why this view looks like this
- **Level rule:** perspective "the persisted data" (one subject area) → *balanced* (SKILL.md §1.2); budget ≤ 10 classes, used 6.
- **Multiplicities come from the mappings and schema:** `@OneToMany(cascade = ALL)` + nullable FK → composition `0..1` to `0..*`; `@ManyToOne` + `type_id NOT NULL` → exactly `1`; `@ManyToMany` → `0..*` both ends. Arrows show navigability: every mapping is one-directional in the code.
- **Left out:** the three `@MappedSuperclass` bases (no tables; their columns are folded into the subclasses and the note), the `Vets` XML wrapper (not persisted), operations and private helpers (§3: key attributes only, hide what the concern does not need).
- **Constraints as UML constraints** `{unique per owner}`, `{indexed}`, `{≤ 80}` instead of invented stereotypes; no crow's feet, no «table» (§4 UML overrides).
- **Reference schema:** H2 `schema.sql`; MySQL/Postgres variants define the same tables.
- **Checks:** puml-check OK; check_inventory 0 issues. Image review: shortened two attribute constraints that wrapped.
