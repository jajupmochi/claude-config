---
name: parity-restoration
description: When restoring or reconciling one environment to match another (staging↔production, a 1:1 UI restore, mirroring a reference), do NOT eyeball it — enumerate the surface as a component/page PLAN first, then compare each item deterministically so nothing is missed. Classify every difference and route it by direction: reference-side data/behaviour missing on the target → sync it automatically; target-side additions/fixes the reference lacks → list each for the owner to confirm promotion; then report every change and conflict.
scope: universal
rationale: Environment-parity work fails by OMISSION — a component nobody thought to check stays broken (empty section, stale data, a missing table). A plan-first enumeration converts "compare the two" into an auditable checklist where every component is explicitly visited. Classifying by direction prevents two opposite mistakes: silently overwriting a target-side improvement with the reference, and forgetting to carry a reference-side fix over. The direction rule (auto-sync reference→target data, but only LIST target→reference promotions) keeps the human in the loop exactly where a decision is owed.
---

# parity-restoration

> Reconciling env A to env B (staging↔prod, 1:1 restore)? Enumerate every component as a PLAN first,
> compare each deterministically, classify each diff by direction, sync the reference-side gaps,
> list the target-side additions for the owner. Miss nothing by construction.

## Master TOC

- [Rule](#rule)
- [Why](#why)
- [The plan-first strategy](#the-plan-first-strategy)
- [Classifying every difference](#classifying-every-difference)
- [When it applies](#when-it-applies)
- [Relation to other rules](#relation-to-other-rules)

## Rule

For any task of the shape "make staging match production", "restore this 1:1", "mirror this
reference", or "find all the differences and fix them":

1. **Plan first (prevents omission).** Enumerate the full surface as a checklist BEFORE comparing:
   every page/route, every component on it, and the data source (endpoint/table) each component
   depends on. Write the plan down so coverage is auditable. Do not start fixing until the plan
   exists.
2. **Compare each item deterministically** — call the same endpoint on both, compare counts / field
   population / shape; cross-check the underlying store when a UI emptiness is ambiguous. One row per
   plan item; no item skipped.
3. **Classify every difference by direction** and route it (next section).
4. **Report** the per-component parity table, what was auto-synced, the items awaiting an owner
   decision, and any conflict. Include a visual check of the fixed surface.

## Why

Parity work fails silently by omission: the one component nobody remembered to check is the one that
ships broken. A written component plan makes every item explicitly visited — the failure mode
becomes impossible rather than merely unlikely.

## The plan-first strategy

- Derive the component list from the source of truth (the route files, the nav, the schema), not
  from memory or from what happened to render.
- Include easily-forgotten surfaces: footers, "partner"/"popular"/aside sections, empty states,
  and any component whose data comes from a JOIN/mapping table (those break when a middle table
  isn't seeded).
- If the surface is large, the plan doubles as the unit of `incremental-delivery`: fix + ship each
  component as its comparison resolves.

## Classifying every difference

| Difference | Direction | Action |
|---|---|---|
| Reference has DATA the target lacks (under-populated / empty table) | reference → target | **Auto-sync**: copy reference→target (read-only from reference; respect FK order), verify the component then renders it. |
| Reference has CODE/behaviour the target lacks | reference → target | **Auto-bring** to target and report (+ any conflict). |
| Target has an ADDITION or FIX the reference lacks | target → reference | **Do NOT auto-promote.** List each item for the owner to confirm whether to merge to the reference (`main`) + deploy. |

Never modify the reference/production data — it is the read-only source. The target (staging) is
writable.

## When it applies

- Staging↔production reconciliation, "confirm all data/display synced".
- A 1:1 UI restoration against a design or another environment.
- Any "find all differences and fix/report" between two instances of the same system.

## Relation to other rules

- Uses `phased-planning` (the component plan is the phase list) and feeds `incremental-delivery`
  (ship each component as it's reconciled).
- The "list target-side promotions for the owner" branch respects the authorization boundary that
  the pre-edit / production rules enforce.
