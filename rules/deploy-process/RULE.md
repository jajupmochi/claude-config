---
name: deploy-process
description: Every deploy runs one of two processes — standard (deploy entirely via CICD) or emergency (ssh-push direct to the server, github synced afterwards). DEFAULT is standard; a session can be switched to emergency and stays emergency until told. Both share a local-first prefix (modify → test → commit → squash the task's commits when clean). Emergency exists to stop burning CICD minutes and cut commit pollution; it never touches CICD until switched back. Announce which process is active; never switch silently.
scope: universal
rationale: Deploying "however feels quick this time" burns finite CICD minutes, litters history with fix→bug→refix noise, and leaves the three copies of the code (local, server, github) silently out of sync. Naming two explicit processes — one CICD-first, one ssh-first — makes the deploy path a deliberate, announced choice, keeps all three ends reconciled, and gives a clean fallback when CICD is billing-blocked or must be bypassed without abandoning discipline.
---

# deploy-process

> Two processes: **standard** (deploy via CICD) and **emergency** (ssh-push direct, github after).
> DEFAULT is standard. A session can be switched to emergency and STAYS emergency until told.
> Announce which is active; never switch silently.

## Master TOC

- [Rule](#rule)
- [Shared prefix](#shared-prefix-both-processes)
- [Standard process](#standard-process)
- [Emergency process](#emergency-process)
- [Which one, and switching](#which-one-and-switching)
- [Mechanics and hazards](#mechanics-and-hazards)
- [Why](#why)
- [Relation to other rules](#relation-to-other-rules)

## Rule

Pick one of two deploy processes per task-group and **say which one you are using**. The default is
standard. If the user puts the session into emergency mode, every deploy is emergency until they
switch it back — do not revert on your own, and do not silently switch mid-session.

## Shared prefix (both processes)

1. **Modify locally**, on a feature branch, not directly on `main`.
2. **Test for real** (the exact command, real output — no "should pass").
3. **Commit** in small conventional-commit steps.
4. When a task — a single task, or a group of genuinely interdependent tasks — is **fully clean
   locally**, review that task's commits and **squash/merge the noise** before it leaves the machine:
   a `fix → bug → refix` chain collapses to one honest commit, throwaway/WIP commits fold in. Keep the
   history that explains a real decision; drop the history that only records thrashing.

Only after the shared prefix does the process diverge.

## Standard process

1. Investigate what changed on the **server** and on **github**; merge and resolve conflicts so the
   branch is current.
2. **Push to github.**
3. **Deploy entirely via CICD** — let the pipeline build and release. Do not hand-deploy around it.
4. Ensure **every Action is green**. A red or skipped Action is a failed deploy, not a warning.
5. **Verify multi-method, including a visual screenshot** of the changed surface on the deployed
   environment (per `design-artifacts`).
6. Consolidate whatever CICD **genuinely cannot do** (usually only `sudo`-level host steps) into the
   project's **unified deploy doc**, with an explanation of why it is manual.

## Emergency process

Use when CICD must be bypassed — it is billing-blocked, out of minutes, or the user has put the
session in emergency mode. The point is to ship without touching CICD, then reconcile github after.

1. Check the **server-side git and everything around it** — config, content, database — for changes
   made directly on the box; merge and resolve conflicts so you are not about to overwrite real state.
2. **ssh-push the change DIRECT to the server** so that **local == server git**. Update server git over
   ssh (git pull from a bundle / `git apply` a patch / push to a server-side remote) — **never rsync**
   a deploy (it clobbers `.env*` and other server-only files).
3. **Verify on the server, multi-method, including a visual screenshot.** Build THEN restart; a stale
   manifest serves broken assets.
4. **Do NOT touch github yet.** Emergency deploys land on the server first, deliberately.
5. Once the server is verified, **sync github in one shot** so all **three ends — local, server,
   github — hold the same git**. If github gained new pushes or conflicts meanwhile, resolve those
   first, then push.
6. **Do NOT touch CICD/actions during emergency.** Leave a note (a TODO / a line in the deploy doc)
   listing what CICD still needs wired. Wire CICD only when the session switches back to standard, or
   when the user explicitly asks to update CICD.

## Which one, and switching

- **Default is standard.** If nothing was said, deploy standard.
- The user switches the session to **emergency** explicitly ("use the emergency process", "本 session
  用紧急流程"); it then stays emergency for the whole session until they switch back.
- **Announce the active process** at the deploy step ("deploying via the emergency process: …"). The
  process is the user's control dial over CICD spend and prod-touch — surfacing it keeps them in the
  loop.
- **Never silently switch** processes mid-session, and never silently deploy the "other" way because it
  looked faster.

## Mechanics and hazards

- **No rsync deploys.** rsync overwrites server-only files (`.env.local`, secrets) and reads as a fake
  CORS/whatever failure later. Update server git over ssh instead.
- **Build then restart.** A rebuilt bundle behind a still-running old server serves stale/400 chunks
  and never hydrates. Restart the server process after the build.
- **Three-way parity is the emergency invariant.** Emergency is only "done" when local, server, and
  github agree. A server that is ahead of github is a landmine for the next person who pulls.
- **Read-only deploy keys** mean the server can only pull FROM github, so emergency's direct push uses
  a different channel (patch/bundle/server remote), not a push the read-only key would reject.

## Why

Deploying ad-hoc burns finite CICD minutes, pollutes history with thrash commits, and lets local,
server, and github drift apart silently. Two named processes make the deploy path a deliberate,
announced choice, keep all three copies reconciled, and give a disciplined fallback when CICD is
unavailable — without ever abandoning "verify for real, including visually."

## Relation to other rules

- **`incremental-delivery`** — ship each independent, verified piece as it lands; deploy-process is
  *how* that ship happens.
- **`commit-discipline`** — conventional commits; deploy-process adds the squash-when-clean step.
- **`root-cause-before-fix`** / **`regression-test-on-bugfix`** — the "fully clean locally" gate.
- **`design-artifacts`** — the visual-screenshot verification both processes require.
- The project's **unified deploy doc** is where standard records its `sudo`-only steps and emergency
  records its deferred-CICD TODOs.
