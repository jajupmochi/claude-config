## no-ssh-username-probing

Never hammer a host with SSH/`scp`/`sftp` attempts. Get the **exact user, port, and key** from a source of
truth FIRST — deploy config (`deploy.yml`, runbook), a prior session's memory, or **ask the human** — do not
infer them from the hostname or try "likely" values. Then **try exactly once** (`-o BatchMode=yes -o
ConnectTimeout=10`). On failure, **read the error and diagnose — do not retry blindly**: `Permission denied
(publickey)` = wrong user/key (fix the info, one more try at most, then ask); a timeout/refused on ONLY the
SSH port while other ports answer = you may already be IP-banned (stop, confirm from a different IP, get
unbanned — retrying deepens the ban). **Never loop** through candidate usernames/ports/keys — that is the
brute-force signature fail2ban bans, and the agent shares the human's egress IP, so the ban locks the human
out of their own server too. Confirm-then-connect, never guess-and-hammer. Enforced by the `ssh-guard` hook.
