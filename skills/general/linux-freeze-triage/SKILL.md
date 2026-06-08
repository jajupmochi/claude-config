---
name: linux-freeze-triage
description: Use when a Linux desktop/laptop goes black-screen, frozen, or unresponsive (often after idle, or when running a GPU/video app like Zoom/Chrome), and you must find the REAL cause instead of guessing. Covers ruling out suspend/sleep, NVIDIA driver kernel-vs-userspace version mismatch from auto-upgrades, OOM meltdowns, PCIe link errors, and DPMS/display-wake hangs. Bundles a near-zero-cost watchdog to capture the next freeze and a read-only diagnostic battery. Apply before recommending any fix for a freeze/black-screen.
---

# /linux-freeze-triage

Find the real cause of a Linux freeze / black-screen by evidence, not by guessing from the symptom.

## Master TOC
- [Core discipline](#core-discipline)
- [Step 0: capture before you guess](#step-0-capture-before-you-guess)
- [Step 1: rule out sleep/suspend](#step-1-rule-out-sleepsuspend)
- [Step 2: read the freeze moment](#step-2-read-the-freeze-moment)
- [The usual suspects (ranked)](#the-usual-suspects-ranked)
- [Recovery without losing work](#recovery-without-losing-work)
- [Bundled scripts](#bundled-scripts)
- [War story](#war-story)

## Core discipline
- Do NOT commit to a hypothesis from the symptom alone. A blinking power LED is NOT proof of sleep (it is usually the monitor's no-signal standby). "Happens after idle" is NOT proof of a DPMS/suspend bug.
- Instrument and CAPTURE the next occurrence; let evidence pick the cause.
- A log-churning service (e.g. a unit crash-looping every ~2s) rotates journald so fast that the real freeze logs roll off — find and fix it first, or you will never see the evidence.
- Same failure on BOTH Xorg and Wayland => the cause is BELOW the display server (driver/kernel/hardware); do not blame the compositor.

## Step 0: capture before you guess
Run `diagnose.sh` (read-only battery). Arm `freeze-watch.sh` (near-zero-cost: nice 19 / ionice idle / 60s) so the NEXT freeze is recorded — its last log line is the state at death:
- `NVSMI_FAIL` => GPU fell off the bus / driver broken.
- `DRIVER_MISMATCH ... REBOOT-NEEDED` => NVIDIA driver upgraded without reboot (suspect #1).
- load exploding into the hundreds => meltdown (OOM storm, or mass D-state on a wedged resource).

## Step 1: rule out sleep/suspend (cheap, decisive)
- `journalctl -u systemd-suspend.service`  ("No entries" => never suspended)
- `cat /sys/power/suspend_stats/success /sys/power/suspend_stats/fail`  (0/0 this boot => no suspend)
- `journalctl -k -g "PM: suspend entry"`  (none => not S3/s2idle)
If all empty, it is NOT sleep. Stop chasing suspend/resume (and ignore the blinking LED).

## Step 2: read the freeze moment
- `journalctl --list-boots`; `last -x | grep -iE "reboot|shutdown"` (find the crashed boot, spot unclean resets)
- `journalctl -b -1 -k --since "<HH:MM just before>" --until "<HH:MM>"` and grep:
  `NVRM|Xid|API mismatch|PCIe Bus Error|AER|oom-kill|Out of memory|hung_task|soft lockup|fallen off`
- `ls -A /sys/fs/pstore/` (a captured panic? often EMPTY on a GPU "fell off bus" hard hang — absence is itself a clue)

## The usual suspects (ranked, NVIDIA desktops)
1. **NVIDIA driver kernel-vs-userspace MISMATCH from auto-upgrade.** `unattended-upgrades` upgrades the nvidia driver on disk while the machine runs; the LOADED kernel module stays old. The next GPU client (Xorg / gnome-shell / nvidia-smi, or any GPU app such as Zoom/Chrome video) hits `NVRM: API mismatch: the client ... has the version <new>, but this kernel module has the version <old>` => clients crash-loop => session drops to the login screen, load spikes, OOM, black screen.
   - Detect: `cat /proc/driver/nvidia/version` (loaded) vs `modinfo -F version nvidia` (on disk) vs `nvidia-smi --query-gpu=driver_version` (userspace). Any divergence => reboot is overdue.
   - Confirm: `grep -i nvidia /var/log/apt/history.log` (frequent auto-upgrades), `apt-mark showhold | grep nvidia` (not held), uu enabled in `/etc/apt/apt.conf.d/20auto-upgrades`.
   - FIX: stop auto-upgrading nvidia; update it manually then reboot. Add to `Unattended-Upgrade::Package-Blacklist` in `/etc/apt/apt.conf.d/50unattended-upgrades`: `"nvidia-";` `"libnvidia-";` `"linux-modules-nvidia-";`. Prefer this over `apt-mark hold linux-modules-nvidia-*` (a held module pkg can leave a freshly-installed kernel with no matching nvidia module). Do NOT enable uu Automatic-Reboot if long jobs run.
2. **OOM meltdown.** `journalctl -b -1 | grep -iE "oom-kill|Out of memory"`. Load explodes; OOM kills chrome/gnome-shell. Amplified by tiny swap. Mitigate with zram (compressed swap) so memory pressure degrades gracefully; fix whatever leaked or crash-looped.
3. **PCIe link instability.** `pcieport 0000:00:01.0: PCIe Bus Error ... Physical Layer ... RxErr` on the GPU root port. Chronic correctable errors => marginal link, can escalate to "GPU fell off the bus". Fix: reseat the GPU + its power cables, clear dust; test kernel param `pcie_aspm=off`.
4. **DPMS / display-wake hang (milder).** Screen blanks on idle, GPU fails to re-init on wake. Usually RECOVERABLE with a VT switch (Ctrl+Alt+F3 then Ctrl+Alt+F2) — no reboot. Keep `NVreg_PreserveVideoMemoryAllocations=1`.
5. **Genuine suspend/resume failure** — only if Step 1 actually showed suspends.

## Recovery without losing work
- Milder display hang: **Ctrl+Alt+F3 then Ctrl+Alt+F2** (re-inits the display).
- Session crashed to login, or black but machine alive: **SSH in from another device** (if sshd / ssh.socket is up), then `sudo systemctl restart gdm`, or a clean `sudo reboot`. Never long-press the power button if SSH still answers.
- Always run long / agent work inside **tmux** (or screen) so a session crash or `gdm` restart does not kill it; reattach after. For Claude Code, `claude --continue` reloads the conversation after a reboot.

## Bundled scripts
- `diagnose.sh` — read-only battery (model, sleep state, GPU + all three driver versions, suspend history, last-boot OOM/GPU/PCIe, RAM/swap, journald persistence). Run first.
- `freeze-watch.sh` — detached near-zero-cost watchdog; logs GPU + load every 60s and flags `NVSMI_FAIL` / `DRIVER_MISMATCH`. Launch: `nohup setsid nice -n 19 ionice -c3 bash freeze-watch.sh >/dev/null 2>&1 &`. After the next freeze, read `~/freeze-watch.log` (last line = death state). Stop: `pkill -f 'freeze-watch[.]sh'`.

## War story (why the discipline matters)
On an RTX 3070 desktop the symptom ("black after idle, blinking LED, power tap dead, long-press to reboot") screamed "S3 will not wake". It was not: `systemd-suspend.service` had zero entries and `suspend_stats` was 0/0. Two wrong guesses later (sleep, then Wayland) the watchdog caught the truth: `unattended-upgrades` had bumped the NVIDIA driver (580.142 -> 580.159.03) without a reboot; opening Zoom then hit the API mismatch, crash-looped the session, OOM'd, black screen. A crash-looping `ollama` unit had been rotating the journal every 2s and erasing the evidence. Lessons, in order: rule out sleep first, fix the log-churner, instrument and capture, then check the driver version mismatch.
