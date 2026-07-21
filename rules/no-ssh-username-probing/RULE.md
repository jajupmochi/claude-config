---
name: no-ssh-username-probing
description: Never guess/probe SSH usernames against a host. Find the EXACT user first (deploy config, the human, or `ssh -v`), try ONCE, and on failure ask — do not loop. Probing usernames trips fail2ban and IP-bans you (and, because an agent shares its human's egress IP, bans the human too). Enforced by the ssh-guard hook.
scope: universal
rationale: A wrong-username SSH loop is indistinguishable from a brute-force attack to fail2ban's sshd jail. It bans the source IP on the SSH port while leaving every other port open — so it masquerades as a host outage, and the recidive jail escalates repeat offenders to week-long bans. The agent and its human usually share one NAT/egress IP, so the self-inflicted ban locks the human out of their own server. The cost of confirming the username up front is one lookup; the cost of probing is losing SSH access for hours to days.
---

# no-ssh-username-probing

> Don't guess SSH usernames. Confirm the exact user, try once, and if it fails **ask** — never loop through candidate usernames against a host.

## Master TOC

- [Rule](#rule)
- [The incident this exists for](#the-incident-this-exists-for)
- [Why it's dangerous](#why-its-dangerous)
- [How to do it right](#how-to-do-it-right)
- [Enforcement](#enforcement)
- [Relation to other rules](#relation-to-other-rules)

## Rule

Before SSHing (or `scp`/`sftp`) to a host:

1. **Get the exact username, port, and key from a source of truth** — deploy config (`deploy.yml` `DEPLOY_USER`, CI secrets doc), the project's runbook, a prior session's memory, or **ask the human**. Do not infer any of them from the hostname or try "likely" values. (This host's answer, recorded: `deploy-user@…` on port `2222`, key-based.)
2. **Try exactly once** with that user (`-o BatchMode=yes` so a wrong key fails fast instead of hanging on a password prompt).
3. **On failure, STOP and ask.** Read the actual error (`Permission denied (publickey)` = wrong key/user; `Connection refused`/timeout on only the SSH port = you may already be banned — see below). Do **not** try a second, third, … username.
4. **Never run a loop** (`for u in root admin ubuntu …; do ssh $u@host; done`) against a real host. That is the exact brute-force signature fail2ban bans.

If the SSH port is refused from your IP but other ports on the host are open, assume **you are IP-banned**, not that the host is down. Confirm by testing the SSH port from a *different* IP (a bastion/jump host); a TCP-only connectivity test carries no auth and won't deepen the ban. Then have someone unban your IP from the host (`fail2ban-client unbanip <ip>`) — do not keep retrying, which extends the ban.

## The incident this exists for

**2026-07-17.** An agent needed to read a production box's database. Not knowing the SSH user, it tried several candidate usernames in succession against the prod host on port 2222. fail2ban's sshd jail counted the failed auths and banned the shared egress IP (`203.0.113.10`) on the SSH port. Every other port (the app on :5000, staging on :38xxx) stayed open, so it first looked like a host problem — but a TCP test from a bastion showed :2222 open from *there*. It was a self-inflicted ban, and it also locked out the human, whose laptop shared that egress IP. The correct username (`deploy-user`) was sitting in the repo's `deploy.yml` the whole time.

## Why it's dangerous

1. **fail2ban can't tell you from an attacker.** N failed auths from one IP = ban, whatever your intent.
2. **The ban is SSH-port-specific**, so it disguises itself as an outage and wastes debugging time.
3. **Recidive escalation**: repeat offenders get progressively longer bans (hours → a week).
4. **Shared egress IP**: the agent's ban is the human's ban. You break the thing you were trying to use, for both of you.

## How to do it right

```bash
# 1. Find the user (don't guess):
grep -RniE 'DEPLOY_USER|ssh .*@|User ' deploy/ .github/ docs/    # or just ask the human

# 2. One attempt, fail-fast:
ssh -o BatchMode=yes -o ConnectTimeout=10 <the_confirmed_user>@host -p <port> 'whoami'

# 3. If it fails: read the error, ask the human. Do NOT try another username.
```

## Enforcement

The **`ssh-guard`** PreToolUse(Bash) hook enforces this deterministically: it records the username used per host and **blocks the 2nd distinct username to the same host within a short window** (the probing signature), with a message pointing back here. Same-user retries pass. A genuinely-separate second account can be allowed once via a one-shot override file. Install it from `hooks/ssh-guard/` (see that hook's README).

## Relation to other rules

- Pairs with **[block-env-read]** and the review-gate's remote-publishing block as the "deterministic guard rails that stop a known-costly mistake before it happens" family.
- Complements **[pre-edit-confirmation]**: both replace "guess and see" with "confirm, then act" — here the stakes are an IP ban rather than a wrong edit.
