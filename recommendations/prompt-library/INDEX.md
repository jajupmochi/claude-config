# Prompt library

> Reusable prompts, de-privacy'd and tagged by scenario — copy the Optimized block, or read When to use to decide whether this is the right prompt for the job.

## Master TOC

- [All prompts](#all-prompts)
- [By scenario](#by-scenario)

## All prompts

18 reusable prompt(s). Each file holds the original prompt, an optimized rewrite, and when to use / when not to use it.

| title | scenarios | when to use | source | file |
|---|---|---|---|---|
| Deploy through CI only, never by hand | deployment,infra,policy | Use on any project with more than one contributor, or any deployed system where drift between environments is… | claude-code | `prompts/deploy-through-ci-only-never-by-hand.md` |
| Documentation completeness audit and backlog consolidation | audit,docs,planning | Use at a natural checkpoint, when several features have landed quickly and you suspect the docs and the backl… | claude-code | `prompts/documentation-completeness-audit-and-backlog-consolidation.md` |
| Exhaustive subsystem documentation for mixed audiences | docs,architecture,handover | Use when a subsystem turned out to be much harder than expected and the knowledge is spread across commits, c… | claude-code | `prompts/exhaustive-subsystem-documentation-for-mixed-audiences.md` |
| In-app manual, guided tour and bug reporting | product,onboarding,docs,ui | Use when a product is about to go to testers who are not the people who built it. | claude-code | `prompts/in-app-manual-guided-tour-and-bug-reporting.md` |
| Inspect a dataset schema without reading the data | data-platform,privacy,analysis | Use whenever you need an agent to reason about a dataset that it must not see. | claude-code | `prompts/inspect-a-dataset-schema-without-reading-the-data.md` |
| Multi-part feature update brief | feature-spec,planning,agent-tooling | Use when you have accumulated several unrelated changes for one project and want them handled in a single aut… | claude-code | `prompts/multi-part-feature-update-brief.md` |
| Package a proven workflow as a reusable skill | skill-authoring,agent-tooling,docs | Use right after you have manually proven a workflow that you expect to repeat, while the failures are still f… | claude-code | `prompts/package-a-proven-workflow-as-a-reusable-skill.md` |
| Plan feature coverage across every dataset and model first | research,planning,coverage | Use when a feature was built against one dataset or model and you are about to assume it generalizes. | copilot-vscode | `prompts/plan-feature-coverage-across-every-dataset-and-model-first.md` |
| Port code from a reference project verbatim, with a provenance map | porting,refactor,research-code | Use when adapting a reference implementation — a paper's released code, a sibling repo, an upstream library —… | copilot-vscode | `prompts/port-code-from-a-reference-project-verbatim-with-a-provenance-map.md` |
| Reproduce the server environment locally in Docker | infra,deployment,testing | Use when local development has diverged from the server badly enough that you cannot trust local results, and… | opencode | `prompts/reproduce-the-server-environment-locally-in-docker.md` |
| Rewrite an executive summary for decision makers | writing,pitch,proposal | Use for the summary section of a grant application, investor deck or proposal, especially when a previous dra… | claude-code | `prompts/rewrite-an-executive-summary-for-decision-makers.md` |
| Run the end-to-end test, record baselines, prove reproducibility | testing,verification,research-code | Use for research code where a number only counts if it reproduces. | copilot-vscode | `prompts/run-the-end-to-end-test-record-baselines-prove-reproducibility.md` |
| Separate a tuned hyperparameter from an ablation sweep | research,experiments,config | Use when designing configuration for research code and a parameter has to serve two purposes: something you o… | claude-code | `prompts/separate-a-tuned-hyperparameter-from-an-ablation-sweep.md` |
| Ship changes with clickable local test links and screenshots | frontend,backend,reporting,agent-tooling | Use as a standing instruction for any session that produces API or UI work. | claude-code | `prompts/ship-changes-with-clickable-local-test-links-and-screenshots.md` |
| Standalone HTML report for collaborators from analysis notebooks | reporting,research,collaboration | Use when you need a shareable artifact for people who will not open your notebooks, but you still want the no… | claude-code | `prompts/standalone-html-report-for-collaborators-from-analysis-notebooks.md` |
| Standing rules for how an agent should work | agent-tooling,config,ui | Use once, when you notice you are giving the same corrections in every session. | claude-code | `prompts/standing-rules-for-how-an-agent-should-work.md` |
| Triage a failure batch into a plan table before touching code | bug-triage,planning,research-code | Use when a batch of failures shares one apparent cause and the obvious general fix would paper over per-case … | copilot-vscode | `prompts/triage-a-failure-batch-into-a-plan-table-before-touching-code.md` |
| Turn a session into a router of scoped sub-tasks | orchestration,context,planning | Use at the start of a long-running session that will span many related but separable pieces of work, when you… | claude-code | `prompts/turn-a-session-into-a-router-of-scoped-sub-tasks.md` |

## By scenario

- **agent-tooling** — [Multi-part feature update brief](prompts/multi-part-feature-update-brief.md), [Package a proven workflow as a reusable skill](prompts/package-a-proven-workflow-as-a-reusable-skill.md), [Ship changes with clickable local test links and screenshots](prompts/ship-changes-with-clickable-local-test-links-and-screenshots.md), [Standing rules for how an agent should work](prompts/standing-rules-for-how-an-agent-should-work.md)
- **analysis** — [Inspect a dataset schema without reading the data](prompts/inspect-a-dataset-schema-without-reading-the-data.md)
- **architecture** — [Exhaustive subsystem documentation for mixed audiences](prompts/exhaustive-subsystem-documentation-for-mixed-audiences.md)
- **audit** — [Documentation completeness audit and backlog consolidation](prompts/documentation-completeness-audit-and-backlog-consolidation.md)
- **backend** — [Ship changes with clickable local test links and screenshots](prompts/ship-changes-with-clickable-local-test-links-and-screenshots.md)
- **bug-triage** — [Triage a failure batch into a plan table before touching code](prompts/triage-a-failure-batch-into-a-plan-table-before-touching-code.md)
- **collaboration** — [Standalone HTML report for collaborators from analysis notebooks](prompts/standalone-html-report-for-collaborators-from-analysis-notebooks.md)
- **config** — [Separate a tuned hyperparameter from an ablation sweep](prompts/separate-a-tuned-hyperparameter-from-an-ablation-sweep.md), [Standing rules for how an agent should work](prompts/standing-rules-for-how-an-agent-should-work.md)
- **context** — [Turn a session into a router of scoped sub-tasks](prompts/turn-a-session-into-a-router-of-scoped-sub-tasks.md)
- **coverage** — [Plan feature coverage across every dataset and model first](prompts/plan-feature-coverage-across-every-dataset-and-model-first.md)
- **data-platform** — [Inspect a dataset schema without reading the data](prompts/inspect-a-dataset-schema-without-reading-the-data.md)
- **deployment** — [Deploy through CI only, never by hand](prompts/deploy-through-ci-only-never-by-hand.md), [Reproduce the server environment locally in Docker](prompts/reproduce-the-server-environment-locally-in-docker.md)
- **docs** — [Documentation completeness audit and backlog consolidation](prompts/documentation-completeness-audit-and-backlog-consolidation.md), [Exhaustive subsystem documentation for mixed audiences](prompts/exhaustive-subsystem-documentation-for-mixed-audiences.md), [In-app manual, guided tour and bug reporting](prompts/in-app-manual-guided-tour-and-bug-reporting.md), [Package a proven workflow as a reusable skill](prompts/package-a-proven-workflow-as-a-reusable-skill.md)
- **experiments** — [Separate a tuned hyperparameter from an ablation sweep](prompts/separate-a-tuned-hyperparameter-from-an-ablation-sweep.md)
- **feature-spec** — [Multi-part feature update brief](prompts/multi-part-feature-update-brief.md)
- **frontend** — [Ship changes with clickable local test links and screenshots](prompts/ship-changes-with-clickable-local-test-links-and-screenshots.md)
- **handover** — [Exhaustive subsystem documentation for mixed audiences](prompts/exhaustive-subsystem-documentation-for-mixed-audiences.md)
- **infra** — [Deploy through CI only, never by hand](prompts/deploy-through-ci-only-never-by-hand.md), [Reproduce the server environment locally in Docker](prompts/reproduce-the-server-environment-locally-in-docker.md)
- **onboarding** — [In-app manual, guided tour and bug reporting](prompts/in-app-manual-guided-tour-and-bug-reporting.md)
- **orchestration** — [Turn a session into a router of scoped sub-tasks](prompts/turn-a-session-into-a-router-of-scoped-sub-tasks.md)
- **pitch** — [Rewrite an executive summary for decision makers](prompts/rewrite-an-executive-summary-for-decision-makers.md)
- **planning** — [Documentation completeness audit and backlog consolidation](prompts/documentation-completeness-audit-and-backlog-consolidation.md), [Multi-part feature update brief](prompts/multi-part-feature-update-brief.md), [Plan feature coverage across every dataset and model first](prompts/plan-feature-coverage-across-every-dataset-and-model-first.md), [Triage a failure batch into a plan table before touching code](prompts/triage-a-failure-batch-into-a-plan-table-before-touching-code.md), [Turn a session into a router of scoped sub-tasks](prompts/turn-a-session-into-a-router-of-scoped-sub-tasks.md)
- **policy** — [Deploy through CI only, never by hand](prompts/deploy-through-ci-only-never-by-hand.md)
- **porting** — [Port code from a reference project verbatim, with a provenance map](prompts/port-code-from-a-reference-project-verbatim-with-a-provenance-map.md)
- **privacy** — [Inspect a dataset schema without reading the data](prompts/inspect-a-dataset-schema-without-reading-the-data.md)
- **product** — [In-app manual, guided tour and bug reporting](prompts/in-app-manual-guided-tour-and-bug-reporting.md)
- **proposal** — [Rewrite an executive summary for decision makers](prompts/rewrite-an-executive-summary-for-decision-makers.md)
- **refactor** — [Port code from a reference project verbatim, with a provenance map](prompts/port-code-from-a-reference-project-verbatim-with-a-provenance-map.md)
- **reporting** — [Ship changes with clickable local test links and screenshots](prompts/ship-changes-with-clickable-local-test-links-and-screenshots.md), [Standalone HTML report for collaborators from analysis notebooks](prompts/standalone-html-report-for-collaborators-from-analysis-notebooks.md)
- **research** — [Plan feature coverage across every dataset and model first](prompts/plan-feature-coverage-across-every-dataset-and-model-first.md), [Separate a tuned hyperparameter from an ablation sweep](prompts/separate-a-tuned-hyperparameter-from-an-ablation-sweep.md), [Standalone HTML report for collaborators from analysis notebooks](prompts/standalone-html-report-for-collaborators-from-analysis-notebooks.md)
- **research-code** — [Port code from a reference project verbatim, with a provenance map](prompts/port-code-from-a-reference-project-verbatim-with-a-provenance-map.md), [Run the end-to-end test, record baselines, prove reproducibility](prompts/run-the-end-to-end-test-record-baselines-prove-reproducibility.md), [Triage a failure batch into a plan table before touching code](prompts/triage-a-failure-batch-into-a-plan-table-before-touching-code.md)
- **skill-authoring** — [Package a proven workflow as a reusable skill](prompts/package-a-proven-workflow-as-a-reusable-skill.md)
- **testing** — [Reproduce the server environment locally in Docker](prompts/reproduce-the-server-environment-locally-in-docker.md), [Run the end-to-end test, record baselines, prove reproducibility](prompts/run-the-end-to-end-test-record-baselines-prove-reproducibility.md)
- **ui** — [In-app manual, guided tour and bug reporting](prompts/in-app-manual-guided-tour-and-bug-reporting.md), [Standing rules for how an agent should work](prompts/standing-rules-for-how-an-agent-should-work.md)
- **verification** — [Run the end-to-end test, record baselines, prove reproducibility](prompts/run-the-end-to-end-test-record-baselines-prove-reproducibility.md)
- **writing** — [Rewrite an executive summary for decision makers](prompts/rewrite-an-executive-summary-for-decision-makers.md)
