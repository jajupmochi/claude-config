## incremental-delivery

Ship completed, **independent** pieces as they finish — don't idle-wait for the whole batch. When a
unit of work is verifiable and not directly interdependent with what is still running: **verify for
real → push to `develop`/staging → verify remotely (including a visual screenshot for UI) → report
that piece with the evidence**, so the user can validate early. Do this per piece, not per batch.
Hold only when the next piece genuinely depends on the in-flight one, when it isn't independently
verifiable yet, or when shipping would cross an authorization boundary (production, `main`,
irreversible) — those still need the user's explicit go.
