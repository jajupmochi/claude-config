## deploy-process (standard vs emergency)

Every project deploy runs one of two processes; **DEFAULT = standard**, but a session can be switched to
**emergency** and then stays emergency until the user says otherwise. Announce which one is active; never
switch silently. Both begin identically: local modify → test → commit → once a task (or a group of
interdependent tasks) is FULLY clean locally, review that task's commits and squash/merge the noise
(a fix→bug→refix chain, throwaway commits) before it goes anywhere.

**Before ANY server-touching operation — in BOTH processes, no exceptions:** take a FULL backup first —
code, data (databases + files), config (env + overrides), the running services' state, and anything else
state lives in. Verify the backup exists and is readable BEFORE the first server write (deploy, restart,
migration, config edit). No server mutation without a verified backup to roll back to.

- **Standard:** reconcile server + github diffs (merge/resolve), push to github, deploy **entirely via
  CICD**, ensure every Action is green, verify multi-method **including a visual screenshot**; then fold
  whatever CICD genuinely cannot do (usually only `sudo`) into the project's unified deploy doc.
- **Emergency:** reconcile server-side git + config/content/db (merge/resolve), **ssh-push DIRECT to the
  server** so local == server git, verify on the server multi-method **including a visual screenshot** —
  and **do NOT touch github yet**. Then sync github once so all three ends (local / server / github) match;
  if github gained new pushes/conflicts meanwhile, resolve those first. Do **not** touch CICD/actions in
  emergency — leave a note and wire CICD only when switching back to standard or when explicitly told.

Emergency exists to stop burning CICD minutes and to cut commit pollution when CICD is unavailable or
must be bypassed. Never rsync a deploy (it clobbers env files); update server git via ssh (git pull /
apply / push to a server remote). Pairs with `incremental-delivery`, `commit-discipline`,
`root-cause-before-fix`, and the project's deploy-doc convention.
