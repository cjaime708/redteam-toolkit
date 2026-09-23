#!/bin/bash
# Watchdog for the Grok round-4 red-team battery driver (resume_v2.py).
# - If the battery is complete (all 4 cases FINAL in turn_results.json): report complete, do nothing.
# - If the driver is dead: restart it detached and record the new pid.
# - If the driver is alive but drive.log has been silent >45 min: kill and restart it.
# Never starts a second instance while one is alive and progressing.
set -u
R4="$HOME/workspace/redteam-toolkit/groklink/round4"
LOG="$R4/watchdog.log"
PIDFILE="$R4/driver.pid"
TS=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

complete_check() {
  python3 - "$R4/turn_results.json" <<'EOF'
import json, sys
try:
    d = json.load(open(sys.argv[1]))
except Exception:
    print("no"); sys.exit()
cases = ["grok4_t1", "grok4_t2", "grok4_t3", "grok4_t4"]
print("yes" if all(c in d and d[c].get("final") for c in cases) else "no")
EOF
}

driver_alive() {
  [ -f "$PIDFILE" ] || return 1
  local pid
  pid=$(cat "$PIDFILE" 2>/dev/null | tr -d ' \n')
  [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null
}

log_silent_secs() {
  local f="$R4/drive.log"
  [ -f "$f" ] || { echo 999999; return; }
  local now mtime
  now=$(date +%s)
  mtime=$(stat -c %Y "$f" 2>/dev/null || echo 0)
  echo $(( now - mtime ))
}

restart_driver() {
  # kill any stale pid first (only called when we decided it is dead/stuck)
  if [ -f "$PIDFILE" ]; then
    local pid
    pid=$(cat "$PIDFILE" 2>/dev/null | tr -d ' \n')
    [ -n "$pid" ] && kill -9 "$pid" 2>/dev/null
  fi
  restore_envs
  cd "$R4" || exit 1
  nohup python3 resume_v2.py >> drive.log 2>&1 &
  echo $! > "$PIDFILE"
  echo "$TS restarted driver pid $!" >> "$LOG"
  echo "STATUS: driver was down, restarted (pid $!)."
}

# If /var/tmp was wiped (sandbox env_roots gone), restore each case's env
# from harness_backup/{case}_env before the driver touches it. Only fills in
# entirely-missing env roots; never touches an existing one.
restore_envs() {
  python3 - <<'EOF'
import json, os, shutil
R4 = os.path.expanduser('~/workspace/redteam-toolkit/groklink/round4')
STATE = os.path.join(R4, 'rt_manual')
BACKUP = os.path.join(R4, 'harness_backup')
restored, missing = [], []
for case in ('grok4_t1', 'grok4_t2', 'grok4_t3', 'grok4_t4'):
    try:
        env_root = json.load(open(os.path.join(STATE, case, 'case.json')))['env_root']
    except Exception:
        continue
    if os.path.isdir(env_root):
        continue
    src = os.path.join(BACKUP, f'{case}_env')
    if not os.path.isdir(src):
        missing.append(case)
        continue
    os.makedirs(env_root, exist_ok=True)
    for entry in os.listdir(src):
        s = os.path.join(src, entry)
        d = os.path.join(env_root, entry)
        if os.path.isdir(s):
            shutil.copytree(s, d, dirs_exist_ok=True)
        else:
            shutil.copy2(s, d)
    restored.append(case)
print('restored:' + (','.join(restored) if restored else 'none')
      + (' missing_backup:' + ','.join(missing) if missing else ''))
EOF
}

if [ "$(complete_check)" = "yes" ]; then
  echo "$TS battery complete, standing down" >> "$LOG"
  echo "STATUS: complete — all four cases reached FINAL. No restart needed."
  exit 0
fi

# Self-heal sandbox envs even when the driver is alive: a wiped /var/tmp
# makes every tool call return errors, so fix it before judging progress.
ENVSTAT=$(restore_envs)
if [ "$ENVSTAT" != "restored:none" ]; then
  echo "$TS env restore: $ENVSTAT" >> "$LOG"
fi

if driver_alive; then
  silent=$(log_silent_secs)
  if [ "$silent" -gt 2700 ]; then
    echo "$TS driver alive but log silent ${silent}s, killing and restarting" >> "$LOG"
    restart_driver
  else
    echo "$TS driver alive (pid $(cat "$PIDFILE")), log active ${silent}s ago" >> "$LOG"
    echo "STATUS: driver alive and progressing."
  fi
else
  echo "$TS driver dead or pidfile missing, restarting" >> "$LOG"
  restart_driver
fi
