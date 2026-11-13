# Domain recipes (what the field tests taught)

Each recipe was learned by building small/medium/large samples with this skill (see `samples/*/NOTES.md` in the repo).
General rules that came out of every domain:
- **Link flows to the zone/container, not its members**, unless the member matters. This fixed almost every "edge through the title" report.
- **Size is edges and boundaries too, not just nodes.** 12 nodes with 15 flows and 4 boundaries took 10 rounds. For a 16:9 slide: ≤ 12 nodes, ≤ 12-15 edges, ≤ 3-4 containers. puml-check prints `busy` above that.
- **Rows beat columns for broad graphs**: top-to-bottom, `->` (same rank) inside a row, `-->` between rows. Flip arrowheads (`a <-- b`) for upward flows so rows hold.
- **Pairs stack with `-->`, sit side by side with `->`** (top-to-bottom): primary/standby databases, A/B paths. In the AWS field test a data tier went from 2.13 to 1.32 by changing the pair edges from `->` to `-->`.
- **`-right->`, `-left->` and hidden `right` links do not reorder nodes inside clusters** (they only set `minlen=0`). Reorder declarations instead, or restructure.
- **Overview + details**: overview with zones as nodes (≤ 15), one detail per zone/layer/stage, numbered consistently, `<<muted>>` "(see X)" stub nodes for cross-references, legend naming the detail files.
- **Second semantic class**: `.accent` (blue) for the one thing to look at, `.alert` (red) for gates / PII / risk, `.muted` for context. Always add a legend when a class carries meaning.

## Network: perimeter / boundary (`puml-new network`)
- Zones = `rectangle "Name\nCIDR" as z <<zone-dmz>> { ... }` with the zone classes from the template (untrusted red, DMZ orange, internal green, restricted purple, external dashed grey). Devices = `node`. Firewall = `<<accent>>`.
- HA pair: one rectangle "FW pair (HA)" holding both nodes joined with a plain `fwa - fwb`. Never label that same-rank link: the label is struck by its own line. Put "active / standby" in node labels.
- Dual uplinks: two labelled edges from the same pair (`inet --> fw : ISP A`, `: ISP B`), or fold the ISPs into one edge label; do not model each ISP as a node unless it matters.
- Edge labels = protocol/port only (`HTTPS 443`, `IPsec`). Port lists belong in the node label (`WAF / reverse proxy :443`).
- External clouds (M365, SaaS) on their own rank or side, never in the DMZ row (it reads as "inside the DMZ").
- Large networks split by site and by layer: physical fabric / logical VLAN map / policy (firewall rules as edges between VLAN nodes, "everything else denied" in a note) / wireless / servers.
- Legend tables (`|= a |= b |`) render heavy black cell borders; prefer plain legend lines or a colour swatch cell `|<#FFF7ED>   | DMZ |`.

## Network: intranet / VLANs
- VLAN as `rectangle "VLAN 20 Workstations\n10.10.20.0/24"`; host octets as a second line in the node label (`"DC1\n.10"`), not on edges. Trunks: edge label with the VLAN list.
- Switch stacks / MLAG pairs: nested rectangle with the two members joined `a - b`.
- Keep physical (switch topology) and logical (VLAN membership) in separate diagrams past ~12 nodes.
- `@startnwdiag` ... `@endnwdiag` is an alternative for a VLAN bus map: one horizontal bus per network, stacked. It cannot be steered (no direction, no spacing), network names must be identifiers (`network v10 { description = "VLAN 10" }`), `nwdiag {}` inside `@startuml` is rejected on 1.2026.x, and `address = ".10"` text is struck by the link line (use `description`). Portrait by nature; fine for print, not for 16:9.
- Under `left to right direction`, a same-rank pair inside a rectangle can come out in reverse declaration order; swap the declarations if it does.

## CI/CD pipelines
- Flow of a pipeline: `activity` with `fork` for parallel jobs, `partition "Playwright matrix" { fork ... }` for a matrix, `note right : matrix: Node 20, 22` when the matrix is not worth drawing. Infrastructure of the pipeline: `component`, rows per environment.
- **Gates**: put the happy path inside `then` and the exit (`stop`) in `else`; an empty-else early exit grows a long bypass edge (0.36 → 0.79 ratio in the field test). Mark the gate `<<alert>>` and say so in the legend.
- Activity diagrams cannot go left-to-right; a 7-step pipeline with one fork reaches ~1.33:1 at best. For a 16:9 slide, draw the pipeline as a component/LR diagram of stages, or accept the `aspect` info when it fits the slot unscaled.
- `kill` inside nested `if`/`repeat` may render nothing; use `stop`. The `repeat while (x?) is (yes) not (no)` labels disappear under `skinparam conditionStyle diamond`, which is why the template does not set it.
- Fork/join bars need `activityBar { BackgroundColor #475569 }` (in the template) or they vanish against the light fills.
- Large pipelines: overview with one node per stage (numbered) plus one activity diagram per stage (7-12 actions, letter portrait).

## Data-flow diagrams (`puml-new dfd`)
- Notation: process = `usecase` (ellipse, numbered 0 / 1 / 1.1), external entity = `rectangle`, store = `database` (`storage` looks like a process), boundary = `rectangle <<boundary>>` (dashed, transparent), PII flow = `-[#D55E00,bold]->` with "(PII)" in the label and a legend line `<color:#D55E00><b>orange</b></color> = PII`.
- Levels: level 0 (one process, entities, stores) then one level-1 per process (7-9 nodes). Never both in one diagram.
- Draw **writes** to stores and say "reads omitted" in the legend; read-backs loop around the whole diagram. Draw a read
  when it is a process's only input (`p2 <-- db : open cases`, arrowhead flipped so the store stays below).
- Hand-offs between processes in one zone go through the store, not a same-rank `p1 -> p2`: Graphviz can place another
  process between them, and the flow loops over the zone title. In the dfd template on Graphviz 2.43 that loop grew the
  diagram to 573x610, past a 16:9 slot; the store read instead gave 698x541 (527x541 on 15.1.1; both Ubuntu CI with
  Liberation Sans, PlantUML 1.2026.8; 527x519 on macOS).
- Rows by zone (Public / App / Data / Third party) top-to-bottom with flipped arrowheads for upward flows.
- Boundary titles are centred at the top; a flow entering from above crosses the title. What cleared all three crossings in the template, in combination: one-word zone titles (`App`, `Data`), cross-boundary flows linked to the zone rectangle, and the store that receives most flows declared last so it sits away from the title centre. `package`/`frame` titles and `HorizontalAlignment` made no difference. Dashed boundary + dashed "async" arrows clash; use a colour for one of them.


## VMware / vSphere with SAN
- Shapes: `node` = hosts, switches, vCenter, appliances; `package` = clusters, vDS, VM groups, sites; `database` = arrays, LUNs, datastores; `cloud` = WAN. A `node` inside a `node` (array holding controllers) renders fine.
- Redundant A/B paths, one idiom per zoom level: overview = "A / B" in the node name and one edge; compute = a borderless "ToR pair (MLAG)" package instead of a labelled peer-link edge; storage = two switch nodes with fabric A edges `-[#0072B2]->` solid and fabric B `-[#E69F00,dashed]->` plus a legend. Never label the pair link itself.
- Port groups = components inside the vDS package; pNICs as edge labels (`vmnic0`), not nodes.
- Role columns under left-to-right: management + VMs | vDS | hosts | ToR + FC | array, every edge pointing right.
- **Fold a chain** when both directions fail the aspect check: make 1-2 unlabelled pair edges same-rank (`->`) and move their text into the node name (4.89 → 1.55 in the field test). A labelled `->` under left-to-right is vertical and strikes its own label.
- Linking to a package routes through an invisible anchor inside it, which can scatter its members (odd 2x2 or triangle layouts, empty space) under left-to-right. Prefer it when the package has one member or when the edges would otherwise cross titles; otherwise link the member that really receives the flow.
- Member layout under left-to-right: `a -[hidden]- b` gives a row (next rank); `b -[hidden]right- a` gives a column (same rank, written bottom-to-top). Real edges attached to the members override this.
- Large estates: overview (sites, clusters, arrays as 12 nodes) + compute/network, storage fabric, DR replication details.

## Kubernetes
- `node "Kubernetes cluster"` holding `rectangle "ns: prod"` namespaces (logical boundary) keeps nesting at 2. Ingress controller (platform, cluster-scoped) and Ingress resource (namespaced) are different nodes.
- `storage` renders as a stadium and becomes a bracketed box in PDF; use `database` for PVCs/object storage with the kind in the label.
- Icons: `!include <kubernetes/k8s-sprites-unlabeled-25pct>` then `<$deploy,scale=0.5,color=#326CE5>` (the 25pct sprites are ~68 px with dark square corners at 1x; scale 0.5 fixes both). Never put a sprite in a container title (it grows the title and edges cross it). Sprite names: render `listsprites` after the include. Icons add 20-45% height; re-check the aspect.
- Namespace detail is naturally layered (Ingress → Service → Deployment → config/PVC → StorageClass): top-to-bottom for print, left-to-right with same-rank unlabelled edges for slides.
- Large platforms: cluster overview (≤ 12 nodes, link to namespaces not members) + one diagram per namespace + platform services (GitOps, cert-manager, monitoring).

## Cloud (AWS) deployment (`puml-new deployment`)
- **Nesting:** region > VPC > AZ > subnet is 4 levels; the limit is 2. Draw the VPC with public and private subnets as its containers, and put the AZ in the node label (`api service\n2-6 tasks, 2 AZs`). Draw AZs as boxes only in a detail diagram about failover.
- **`rectangle "AWS (production)"`, not `cloud`,** for the provider boundary: the cloud outline is bumpy and wider, and nodes near its edge straddle it.
- Edge to the VPC or subnet container (`users --> vpc`), not to each member, unless the member matters; the same rule as zones.
- Push sinks (S3, SES, external providers) out with `--->`; a 0.94 tower became 1.64 in the field test. Move "who does what" into the node (`SQS jobs\napi enqueues, worker consumes`) instead of two labelled edges.
- Slide size: merge pairs that say the same thing (two NAT gateways, a queue and its DLQ, a primary and its standby) into one node with both names.
- A worker that writes to several sinks (S3, SES, SQS) bundles its edges into one trunk with stacked labels (puml-check: `bundled-edges`). Give each sink its own row (`--->` for one of them) or move "writes PDFs, sends email" into the worker node.
- Large estates: overview, then one diagram per layer (edge, network, compute, data, operations).
- **Icons** (all offline, from the jar): `!include <awslib/AWSCommon>` first (without it the next include fails with a syntax error), then one include per service, e.g. `<awslib/NetworkingContentDelivery/CloudFront>`, `<awslib/Database/RDS>`, `<awslib/Containers/Fargate>`, `<awslib/ApplicationIntegration/SimpleQueueService>`. The sprite name is the file name: `rectangle "<$CloudFront,scale=0.5,color=#ED7100>\nCloudFront" as cf` (or the bracket form `[<$RDS,scale=0.5>\nRDS]` without quotes inside, which would print). Put the includes **before** the house `<style>` block: AWSCommon sets its own arrow colours and fonts, and the later style block wins. Names follow the AWS category folders. Rendered on 1.2026.8: `NetworkingContentDelivery/` `Route53`, `CloudFront`, `ElasticLoadBalancing`, `ElasticLoadBalancingApplicationLoadBalancer`, `VPCNATGateway`, `VPCEndpoints`; `Containers/` `Fargate`, `ElasticContainerService`, `ElasticContainerRegistry`; `Database/` `RDS`, `ElastiCache`; `Storage/SimpleStorageService`; `ApplicationIntegration/` `SimpleQueueService`, `SimpleNotificationService`; `BusinessApplications/SimpleEmailService`; `SecurityIdentityCompliance/` `WAF`, `SecretsManager`, `CertificateManager`; `ManagementGovernance/CloudWatch`. These do **not** exist: `Compute/Fargate`, `Containers/ECS`, `NetworkingContentDelivery/ApplicationLoadBalancer`, `NATGateway`. Render once to confirm any other guessed path. Icons add about 25% height at scale 0.5.

## PDF export caveats (all domains)
Fonts are not embedded, bold is lost, Unicode box-drawing glyphs in legends vanish (WinAnsi Type1), `storage` draws as a bracketed box. For print deliverables prefer the 300 dpi PNG or convert the SVG with another tool; keep legends ASCII.
