# Catalog cheat sheet

Read the YAML under `knowledge/` when a field is missing. This page lists legal viewpoint ids. The model chooses one; these tables do not score a winner.

CIAO-aligned catalog ids only: `context`, `cnc-runtime`, `module-decomposition`, `code-mapping`, `decision-record`, `allocation-deployment`.

## Role aliases

| User says | canonical_role |
|---|---|
| software developer, developer, dev | member-of-development-team |
| integration tester, tester, qa | tester-and-integrator |
| software architect | current-and-future-architect |
| devops engineer, sre, operator | infrastructure-support-personnel |
| database engineer, dba | analyst |
| business analyst, product owner | customer |
| newcomer, new contributor | new-stakeholder |

## Role → required viewpoints

| Role | required | optional |
|---|---|---|
| member-of-development-team | module-decomposition, cnc-runtime, code-mapping | |
| tester-and-integrator | code-mapping | context |
| current-and-future-architect | cnc-runtime, decision-record, context | allocation-deployment |
| infrastructure-support-personnel | allocation-deployment, cnc-runtime | code-mapping |
| analyst | context, allocation-deployment | |
| customer | context | |

## Viewpoint defaults

| id | view_type | diagram_language |
|---|---|---|
| context | context_view | mermaid |
| module-decomposition | component_view | plantuml |
| cnc-runtime | component_view | plantuml |
| code-mapping | class_view | plantuml |
| allocation-deployment | deployment_view | plantuml |
| decision-record | component_view | mermaid |
