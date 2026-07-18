## Design modes (prototyping vs scaling)

Two modes with opposite defaults, so settle which one a substantial build is in before starting it.

- **Prototyping** — get a working version fast. High agent autonomy, minimal HITL (approve at milestones), changes land as whole features rather than small reviewed steps, breadth of tests may be deferred. Fits new ideas, throwaway spikes, exploration.
- **Scaling / 精修** — land it correct, stable and deployable. Bounded autonomy, heavy HITL (approve edits, review diffs, confirm risky steps), small reviewed reversible steps, full coverage of bugs, edge cases, boundaries and deployment. Fits real deployment, shared or critical code, refactors.
- **Ask which mode applies** before a substantial build. If the user's message already implies one ("just spike it" → prototyping; "harden this for prod" → scaling), state your read and proceed instead of asking. The ask is a default that `autorun-mode` waives, where the mode defaults to scaling for anything that ships.
- **They mix.** A prototyping run often needs scaling for one delicate part, a tricky bug or a data boundary. A scaling run often needs a quick spike or a bulk automated refactor. Pick the mode per sub-task.
- **Switching mode mid-task normally needs the user's explicit OK** — the HITL level is their control dial, so never silently drop them out of the loop or into it. Under `autorun-mode` the switch is pre-authorised, so report it rather than pausing for it.
- **Capability floor** — a model without strong autonomous execution (DeepSeek-flash and similar low tier) runs in scaling mode, or gets enough harness to compensate (strict templates, per-step verification via `task-orchestrator`). Never hand it a prototyping "take it away" brief it cannot safely execute.
- In scaling mode `pre-edit-confirmation` and `phased-planning` are in full force. Prototyping pre-authorises more autonomy, but it never authorises faking a run or skipping the real run behind a "works".
