#!/usr/bin/env bash
# Ultra-light freeze watchdog (v3): near-zero footprint. Part of the linux-freeze-triage skill.
#   - 60s poll; runs at nice 19 + ionice idle (yields to everything)
#   - logs GPU + load; if nvidia-smi hangs/fails => NVSMI_FAIL (GPU off bus / driver broken)
#   - DRIVER MISMATCH DETECTOR: compares the LOADED nvidia kernel module
#     (/proc/driver/nvidia/version) vs the ON-DISK module (modinfo). If they differ,
#     a driver upgrade landed without a reboot -> logs 'DRIVER_MISMATCH ... REBOOT-NEEDED'.
#     Works even when nvidia-smi is already broken by the mismatch. Reboot when you see it.
#   - self-trims log to 3000 lines (~240 KB).
# Launch:  nohup setsid nice -n 19 ionice -c3 bash freeze-watch.sh >/dev/null 2>&1 &
# Stop:    pkill -f 'freeze-watch[.]sh'      Log:  ~/freeze-watch.log
LOG="$HOME/freeze-watch.log"
INTERVAL=60
MAXLINES=3000
echo "=== freeze-watch v3 started $(date -Is) pid=$$ interval=${INTERVAL}s ===" >> "$LOG"
i=0
while true; do
  ts=$(date -Is)
  gpu=$(timeout 8 nvidia-smi --query-gpu=utilization.gpu,memory.used,memory.total,temperature.gpu,power.draw \
        --format=csv,noheader,nounits 2>/dev/null)
  rc=$?
  if [ "$rc" -ne 0 ] || [ -z "$gpu" ]; then gpu="NVSMI_FAIL_or_TIMEOUT(rc=$rc)"; fi
  warn=""
  loaded=$(grep -oE '[0-9]{3}\.[0-9]+(\.[0-9]+)?' /proc/driver/nvidia/version 2>/dev/null | head -1)
  ondisk=$(modinfo -F version nvidia 2>/dev/null | head -1)
  if [ -n "$loaded" ] && [ -n "$ondisk" ] && [ "$loaded" != "$ondisk" ]; then
    warn=" | DRIVER_MISMATCH loaded=$loaded ondisk=$ondisk REBOOT-NEEDED"
  fi
  printf '%s | load=%s | gpu=%s%s\n' "$ts" "$(cut -d' ' -f1-3 /proc/loadavg)" "$gpu" "$warn" >> "$LOG"
  i=$((i + 1))
  if [ "$((i % 200))" -eq 0 ] && [ -f "$LOG" ]; then
    tail -n "$MAXLINES" "$LOG" > "$LOG.tmp" 2>/dev/null && mv "$LOG.tmp" "$LOG"
  fi
  sleep "$INTERVAL"
done
