# uml-view worked examples (subject: spring-projects/spring-petclinic @ 500158f, cloned to ~/t2v-subjects/vendor/spring-petclinic)

- `component-overview/`: software architect, whole system → overview component view (5 elements); compare with `component-detailed/`.
- `component-detailed/`: developer changing visit scheduling → detailed component view of that path only (8 elements), same system as above.
- `sequence-balanced/`: integration tester, adding an owner → balanced sequence, 4 role lifelines, one `alt` for validation errors.
- `use-case-overview/`: business analyst, what users can do → 6 user goals, one actor (the code has no roles).
- `class-balanced/`: database engineer, persisted data → 6 JPA entities, multiplicities from mappings, key attributes only.
- `deployment-balanced/`: DevOps engineer → the `k8s/` manifests as nodes, execution environments and artifacts.
