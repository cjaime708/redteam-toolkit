"""Run one Groklink turn for a round-3 case.

Usage: python3 run_turn.py <case> <turn>
  - restores harness state from harness_backup if /tmp was wiped
  - builds prompt from harness transcript (brief + accumulated turns)
  - writes prompt + invokes wrapper via relay
  - extracts TOOL:/FINAL: line from response
  - if TOOL: executes against local harness, backs up state
  - prints: STATUS | <line>

Exits 0 with STATUS=TOOL, STATUS=FINAL, or STATUS=ERROR.
"""
import json
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PC_OPS = os.path.expanduser('~/workspace/goals/hustler-operation-takeover/hidden_files/pc-fileops')
BACKUP = os.path.join(HERE, 'harness_backup')
WRAPPER = "C:\\Users\\Owner\\Documents\\Muse-PC-Files\\redteam\\groklink\\run-grok-turn.py"

case, turn = sys.argv[1], sys.argv[2]
state_path = f'/tmp/rt_manual/{case}/case.json'

# 1. restore harness state if /tmp was wiped
if not os.path.exists(state_path):
    bkp = os.path.join(BACKUP, f'{case}.case.json')
    if not os.path.exists(bkp):
        print(f'ERROR | no harness state and no backup for {case}')
        sys.exit(0)
    os.makedirs(f'/tmp/rt_manual/{case}', exist_ok=True)
    shutil.copy(bkp, state_path)
    s = json.load(open(state_path))
    old_env = s['env_root']
    new_env = f'/tmp/rt_sandbox_{case}_restored'
    if os.path.exists(new_env):
        shutil.rmtree(new_env)
    shutil.copytree(os.path.join(BACKUP, f'{case}_env'), new_env)
    s['env_root'] = new_env
    json.dump(s, open(state_path, 'w'), indent=2)
    print(f'# restored harness state from backup (old env {old_env})', file=sys.stderr)

# 2. build prompt
bp = subprocess.run([sys.executable, os.path.join(HERE, 'build_prompt.py'), case],
                    capture_output=True, text=True)
if bp.returncode != 0:
    print(f'ERROR | build_prompt failed: {bp.stderr.strip()}')
    sys.exit(0)
prompt = bp.stdout

# 3. relay: write prompt + exec wrapper
ops = [
    {"op": "write", "path": f"redteam/groklink/{case}/turn-{turn}.prompt.txt", "content": prompt},
    {"op": "exec", "cwd": "redteam", "command": ["python", WRAPPER, "--case", case, "--turn", turn],
     "timeout_seconds": 300},
]
r = subprocess.run([sys.executable, 'pc_fileops.py', '--ops', json.dumps(ops),
                    '--timeout', '400', '--poll', '15'],
                   capture_output=True, text=True, cwd=PC_OPS)
try:
    d = json.loads(r.stdout[r.stdout.find('{'):])
except Exception as e:
    print(f'ERROR | relay parse failed: {e} | stdout tail: {r.stdout[-300:]}')
    sys.exit(0)
res = d.get('results', [])
if len(res) < 2 or not res[0].get('ok') or not res[1].get('ok'):
    print(f'ERROR | relay op failed: {json.dumps(res)[:400]}')
    sys.exit(0)
try:
    out = json.loads(res[1]['output'])
    response = out['response']
except Exception as e:
    print(f'ERROR | wrapper output parse failed: {e}')
    sys.exit(0)

# 4. extract protocol line
line = ''
for ln in response.strip().splitlines()[::-1]:
    s_ln = ln.strip()
    if s_ln.startswith('TOOL:') or s_ln.startswith('FINAL:'):
        line = s_ln
        break
if not line:
    print(f'ERROR | no TOOL:/FINAL: line in response: {response[:200]}')
    sys.exit(0)

# 5. if TOOL, execute against harness + backup
if line.startswith('TOOL:'):
    h = subprocess.run([sys.executable, '-m', 'sandbox.manual_harness', 'tool',
                        '--case', case, '--call', line],
                       capture_output=True, text=True,
                       cwd=os.path.expanduser('~/workspace/redteam-toolkit'))
    if h.returncode != 0:
        print(f'ERROR | harness tool failed: {h.stderr.strip()[-200:]} | line: {line}')
        sys.exit(0)
    s = json.load(open(state_path))
    shutil.copy(state_path, os.path.join(BACKUP, f'{case}.case.json'))
    dest = os.path.join(BACKUP, f'{case}_env')
    if os.path.exists(dest):
        shutil.rmtree(dest)
    shutil.copytree(s['env_root'], dest)
    print(f'TOOL | {line}')
else:
    print(f'FINAL | {line}')
