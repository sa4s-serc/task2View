# Task2View prompts

These are every prompt the pipeline sends to a language model (ADR-006). Everything else in the pipeline is deterministic code. Each file has two parts:

- **Front matter (between the `---` lines):** for people. It says what the call is for, what it receives, what it must return, and which code checks the answer. It is never sent to the model.
- **Body:** the text the model receives. `{{name}}` placeholders are filled in by the caller. Rendering fails if a placeholder is missing or unknown.

| File | Phase | Called from | The model's job | What checks the answer |
|---|---|---|---|---|
| `phase1_interpret.md` | 1 | `phase1/needs.py` | Say what the stakeholder needs to see, in a fixed vocabulary | `validate_needs`: every need, subject and target must be quoted from the goal |
| `phase4_investigate.md` | 4 | `phase4/investigate.py` | Pick where in the repository to start looking | Only symbols and paths that exist in the repository card are kept |
| `phase5_evidence.md` | 5 | `phase5/agent.py` | Read the code with tools and return cited claims | `phase5/verify.py`: file, lines, quoted code and symbol are checked mechanically |

All prompts share one structure:
1. **Role** — who the model is in this step.
2. **Task** — what to produce, and what happens to it next.
3. **Inputs** — the data, clearly delimited.
4. **Rules** — each with the reason it exists.
5. **Output** — the exact JSON shape, with an example.
6. **Check before answering** — a short self-check.

## Shared vocabulary

| Term | Meaning |
|---|---|
| **stakeholder goal** | The free-text request: who the person is and what they need to understand. |
| **information need** | A kind of information the person asks to *see* (for example `collaboration`, `interaction-order`, `data-structure`). There are 23, defined in `knowledge/data/vb/needs.yaml`. Quality attributes (maintainability, security, …) are not needs. |
| **primary / secondary need** | Primary: the request is about it. Secondary: mentioned in passing or implied. Only primary needs can add a view. |
| **subject** | An item the request enumerates (for example "checking seat availability"). Each subject must appear in a view. |
| **target** | The feature or subsystem the request is about. |
| **viewpoint / view** | A viewpoint is a kind of diagram from the Views and Beyond catalog (30 kinds, `viewpoints.yaml`). A view is one diagram drawn from that viewpoint for this request (ISO/IEC/IEEE 42010). |
| **repository card** | The deterministic summary of the repository from Phase 0: files, symbols, dependency graph, entry points, entities, deployment, layers. |
| **symbol** | A named element of the code: class, interface, enum, module or function, with a fully qualified id. |
| **claim** | One small fact about the architecture, with at least one citation. |
| **citation (evidence)** | A file, a line range, and an excerpt copied exactly from those lines. |
| **support** | How well a claim is backed: `observed` (the code shows it), `inferred`, `documented` (docs only), or `weak`. Decided by verification, not by the model. |
