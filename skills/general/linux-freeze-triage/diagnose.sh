#!/usr/bin/env bash
# Read-only freeze / black-screen diagnostic battery. Safe to run anytime. No sudo needed
# for most lines (some journ/PCIe detail is richer with sudo). Part of linux-freeze-triage.
echo "===== MODEL / KERNEL ====="
for f in sys_vendor product_name bios_version bios_date; do printf "%-13s %s\n" "$f" "$(cat /sys/class/dmi/id/$f 2>/dev/null)"; done
echo "kernel: $(uname -r)"

echo; echo "===== SLEEP (rule out suspend first) ====="
echo "mem_sleep     : $(cat /sys/power/mem_sleep 2>/dev/null)"
echo "suspend_stats : success=$(cat /sys/power/suspend_stats/success 2>/dev/null) fail=$(cat /sys/power/suspend_stats/fail 2>/dev/null)"
echo "systemd-suspend history (No entries => never slept):"
journalctl -u systemd-suspend.service --no-pager -n 3 2>/dev/null

echo; echo "===== GPU + DRIVER VERSIONS (any divergence => reboot overdue) ====="
lspci -nnk 2>/dev/null | grep -iEA2 'VGA|3D controller'
echo "loaded kmod : $(grep -oE '[0-9]{3}\.[0-9.]+' /proc/driver/nvidia/version 2>/dev/null | head -1)"
echo "on-disk kmod: $(modinfo -F version nvidia 2>/dev/null)"
echo "userspace   : $(nvidia-smi --query-gpu=driver_version --format=csv,noheader 2>/dev/null)"

echo; echo "===== NVIDIA auto-upgrade risk ====="
echo "uu enabled  : $(grep -h 'Unattended-Upgrade' /etc/apt/apt.conf.d/20auto-upgrades 2>/dev/null | tr -d '\n')"
echo "nvidia held : $(apt-mark showhold 2>/dev/null | grep -c nvidia) package(s)"
echo "recent nvidia driver upgrades:"; grep -h 'nvidia-driver' /var/log/apt/history.log 2>/dev/null | tail -3 | cut -c1-100

echo; echo "===== LAST CRASH WINDOW: OOM / GPU / PCIe (boot -1) ====="
journalctl -b -1 --no-pager 2>/dev/null | grep -iE "oom-kill|Out of memory|NVRM|Xid|API mismatch|PCIe Bus Error|AER:|hung_task|soft lockup|fallen off" | tail -25

echo; echo "===== pstore (captured panic? often empty on GPU hard-hang) ====="
ls -A /sys/fs/pstore/ 2>/dev/null | head || echo "(empty / no access)"

echo; echo "===== RAM / SWAP (OOM amplifier if swap tiny) ====="
free -h; swapon --show 2>/dev/null

echo; echo "===== journald persistent? (needed to keep freeze logs) ====="
[ -d /var/log/journal ] && echo "persistent" || echo "VOLATILE (logs lost on hard reset)"
