## parity-restoration

Reconciling one environment to another (staging↔production, a 1:1 restore, mirroring a reference)?
**Do not eyeball it — plan first.** Enumerate the whole surface as a component/page checklist (every
route, every component, the endpoint/table each depends on — including easily-missed footers,
"partner"/"popular"/aside sections, and JOIN/mapping-table-backed components) BEFORE comparing, so
coverage is auditable. Then compare each item deterministically (counts / field population / shape,
cross-checking the store when ambiguous) and classify every diff by direction: **reference-side
data/behaviour missing on the target → auto-sync it** (read-only from the reference, respect FK
order); **target-side additions/fixes the reference lacks → LIST each for the owner** to confirm
promotion to `main` + deploy. Never modify the reference/production data. Report the per-component
parity table, what was synced, the items awaiting a decision, conflicts, and a visual check.
