# Why this view looks like this
- **Drawn because real files exist:** `k8s/db.yml`, `k8s/petclinic.yml` and a CI job that applies them to a kind cluster (§3: deployment only when the code shows where things run). Level: one deployment → *balanced*; budget ≤ 12, used 7.
- **UML elements only:** `node <<device>>`, `node <<executionEnvironment>>` for cluster and pods, `artifact` for images and the Secret; Services are labels on communication paths, not boxes (§4 UML overrides: no `cloud`/`database`/`rectangle`).
- **Left out:** `docker-compose.yml` (local DBs only, no app container: a second deployment, so a second view), devcontainer/gitpod, and application components (other abstraction level).
- **(unconfirmed):** the app → database path. The manifests set profile `postgres` and mount the binding Secret, but the binding reader lives in the external image `dsyer/petclinic`, not in this repo (see `assumptions` in inventory.json).
- **Residual puml-check warning (1):** `label-on-border` on "mounts (volume)", which sits just under the demo-db Pod border. Shortening the label, putting the Secret on the same rank and switching to top-to-bottom did not fix it (top-to-bottom gave 6 warnings), so the best version was kept per §5.4. The label is still readable in the PNG.
- **Checks:** check_inventory 0 issues.
